/**
 * Setup proxy for development server
 * Handles proxying requests to external services
 * ESM version for consistency with dmv-app
 */
import express from 'express';
import bodyParser from 'body-parser';
import session from 'express-session';
import crypto from 'crypto';
import { reliableFetch, reliableFetchPost } from './reliableFetch.mjs';

// External service URLs
const diagencyAccountUrl = process.env.REACT_APP_ACCOUNT_URL || '';
const tokenUrl = process.env.REACT_APP_TOKEN_ENDPOINT || '';

// Bank agent credentials - stored securely on server side only
const bankAgentId = process.env.REACT_APP_BANK_AGENT_ID || '';
const bankAgentPassword = process.env.REACT_APP_BANK_AGENT_PASSWORD || '';

// Token storage - server-side only, not exposed to client
const tokenStorage = {
    accessToken: '',
    expiresAt: 0
};

// Session configuration
const isProduction = (process.env.NODE_ENV === undefined || process.env.NODE_ENV === 'production');
const sessionConfig = {
    secret: process.env.SESSION_SECRET || crypto.randomBytes(32).toString('hex'),
    resave: false,
    saveUninitialized: false,
    cookie: {
        secure: isProduction, // Require HTTPS in production, allow HTTP for localhost development
        httpOnly: true, // Prevent client-side JavaScript access
        sameSite: isProduction ? 'strict' : 'lax', // Strict in production, lax for localhost
        maxAge: 24 * 60 * 60 * 1000 // 24 hours
    },
    name: 'bank.session.id'
};

/**
 * Sanitize user input for safe logging
 * Prevents log injection attacks by removing control characters
 */
function sanitizeForLog(str) {
    if (typeof str !== 'string') return String(str);
    return str
        .replace(/[\r\n]/g, '') // Remove newlines
        .replace(/[\x00-\x1F\x7F-\x9F]/g, '') // Remove control characters
        .substring(0, 200); // Limit length to prevent log flooding
}

/**
 * Forward a request to an external service and handle the response
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {string} targetUrl - URL to forward the request to
 * @param {Object} options - Additional options for the request
 */
async function callDigitalCredsService(req, targetUrl, options = {}) {
    let result = {};
    result.headers = {};
    try {
        const isImageRequest = req.headers.accept && req.headers.accept.includes('image/');

        const fetchOptions = {
            method: req.method,
            headers: {
                ...req.headers,
                ...(options.headers || {}),
                host: new URL(targetUrl).host
            },
            redirect: options.followRedirects ? 'manual' : 'follow'
        };

        // Add body if present and method supports it
        if (req.body && req.method !== 'GET' && req.method !== 'HEAD') {
            if (req.body instanceof URLSearchParams) {
                fetchOptions.body = req.body;
            } else if (typeof req.body === 'string') {
                fetchOptions.body = req.body;
            } else {
                fetchOptions.body = JSON.stringify(req.body);
            }
        }

        const response = await reliableFetch(targetUrl, fetchOptions, {
            timeout: options.timeout || 10000,
            onRetry: (attempt, error) => {
                console.log(`[BANK-PROXY] Retrying request to ${targetUrl}, attempt ${attempt}. Error: ${error.message}`);
            }
        });

        // Forward response status and headers
        result.status = response.status;
        response.headers.forEach((value, key) => {
            // Skip transfer-encoding and content-encoding headers
            // content-encoding is handled by fetch automatically, so we shouldn't forward it
            // as the body is already decompressed
            if (key !== 'transfer-encoding' && key !== 'content-encoding') {
                result.headers[key] = value;
            }
        });

        // For authorization endpoint, check if we need to redirect
        if (options.followRedirects && response.headers.get('location')) {
            result.headers["location"] = response.headers.get('location');
            return result;
        }

        // Check content type to determine how to handle the response
        const contentType = response.headers.get('content-type') || '';

        // Send response data based on type
        if (options.jsonResponse || contentType.includes('application/json')) {
            result.json = await response.json();
        } else if (isImageRequest || contentType.includes('image/')) {
            // For image responses, send the binary data directly
            const arrayBuffer = await response.arrayBuffer();
            result.buffer = Buffer.from(arrayBuffer);
        } else {
            result.data = await response.text();
        }
    } catch (error) {
        result = handleRequestError(error, options);
    }

    return result;
}

/**
 * Handle errors from forwarded requests
 * @param {Error} error - Error object
 * @param {Object} res - Express response object
 * @param {Object} options - Additional options for error handling
 */
function handleRequestError(error, options = {}) {
    let result = {};
    result.headers = {};

    // For fetch errors, we don't have a response object
    result.status = 504;
    result.json = {
        error: 'Gateway Timeout',
        message: error.message || 'No response received from server'
    };

    return result;
}

export default function setupProxy(app) {
    // Trust proxy - required when behind a reverse proxy (like in production)
    // This ensures secure cookies work correctly with HTTPS termination at the proxy
    app.set('trust proxy', 1);

    // Add body parsing middleware
    app.use(bodyParser.json());
    app.use(bodyParser.urlencoded({ extended: true }));

    // Add session middleware
    app.use(session(sessionConfig));

    // Helper function to get a valid token or refresh if needed
    async function getOrRefreshBankToken() {
        try {
            // Check if we have a valid token that's not expired
            if (tokenStorage.accessToken && tokenStorage.expiresAt > Date.now()) {
                return tokenStorage.accessToken;
            }

            // Create URLSearchParams for the form body
            const formBody = new URLSearchParams({
                client_id: bankAgentId,
                client_secret: bankAgentPassword,
                grant_type: 'client_credentials'
            });

            // Make the token request directly from the server using reliable fetch
            const response = await reliableFetchPost(tokenUrl, formBody, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
            }, {
                timeout: 30000,
                onRetry: (attempt, error) => {
                    console.log(`[BANK-TOKEN] Retrying token request, attempt ${attempt}. Error: ${error.message}`);
                }
            });

            if (!response.ok) {
                throw new Error(`Token request failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();

            // Store the token and calculate expiry time (subtract 60 seconds for safety margin)
            tokenStorage.accessToken = data.access_token;
            tokenStorage.expiresAt = Date.now() + (data.expires_in * 1000) - 60000;

            return tokenStorage.accessToken;
        } catch (error) {
            console.error('Error getting bank token:', error.message);
            throw error;
        }
    }

    // Helper function to forward authenticated requests to diagency
    async function preCallDigitalCredsService(req, res, path) {
        let result = {};
        try {
            const targetUrl = `${diagencyAccountUrl}${path}`;
            const options = { timeout: 30000 };

            // Get the server-side token
            const token = await getOrRefreshBankToken();

            // Always override any Authorization header with our server-side token
            const headers = {
                ...req.headers,
                'Content-Type': 'application/json'
            };
            headers.authorization = `Bearer ${token}`;
            options.headers = headers;

            result = callDigitalCredsService(req, targetUrl, options);
        } catch (error) {
            console.error('Error handling diagency request:', error.message);
            result.status = 500;
            result.json = { error: 'Failed to process request' };
        }
        return result;
    }

    async function sendDigitalCredsResult(res, result) {
        if (result.headers && result.headers["location"] !== undefined) {
            res.redirect(result.headers["location"]);
            return;
        }

        Object.entries(result.headers).forEach(([key, value]) => {
            res.set(key, value);
        });

        if (result.json) {
            res.status(result.status).json(result.json);
            return;
        }

        if (result.data) {
            res.status(result.status).send(result.data);
            return;
        }

        if (result.buffer) {
            res.status(result.status).send(result.buffer);
            return;
        }

        res.send();
        return;
    }

    // Diagency endpoint router with specific allowed paths
    const diagencyRouter = express.Router();

    // POST /verifiable/presentation - Create or get exchange based on session state
    diagencyRouter.post('/verifiable/presentation', async (req, res) => {
        try {
            if (req.session.dcRes) {
                // Session has dcRes - execute GET request
                const exchangeId = req.session.dcRes.json?.id || req.session.dcRes.data?.id;

                if (exchangeId) {
                    console.log(`Signup session already has an exchange created with id '${exchangeId}'.  This will be deleted`);
                    const dcReq = {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    };

                    try {
                        await preCallDigitalCredsService(dcReq, res, `/v1.0/oidvc/vp/exchange/${exchangeId}`);
                    } catch (err) {
                        console.log(`Signup session delete existing exchange with id '${exchangeId}' has failed`);
                        console.error(err);
                    }

                    req.session.dcRes = undefined;
                }
            }

            // Check if session has dcRes from previous execution
            if (!req.session.dcRes) {
                // No active session or no dcRes - execute POST request
                const dcReq = {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: {
                        template_id: process.env.REACT_APP_EXCHANGE_TEMPLATE_ID,
                        with_qr_code: req.body.with_qr_code || false,
                    }
                };

                const dcRes = await preCallDigitalCredsService(dcReq, res, '/v1.0/oidvc/vp/exchange');

                // Store the result in session
                req.session.dcRes = dcRes;

                // Send response
                sendDigitalCredsResult(res, dcRes);
            } else {
                // Session has dcRes - execute GET request
                const exchangeId = req.session.dcRes.json?.id || req.session.dcRes.data?.id;

                if (!exchangeId) {
                    return res.status(400).json({
                        error: 'Bad Request',
                        message: 'Exchange ID not found in session'
                    });
                }

                const dcReq = {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                };

                const dcRes = await preCallDigitalCredsService(dcReq, res, `/v1.0/oidvc/vp/exchange/${exchangeId}`);

                // Update session with new response
                req.session.dcRes = dcRes;

                // Send response
                sendDigitalCredsResult(res, dcRes);
            }
        } catch (error) {
            console.error('Error in POST /verifiable/presentation:', error);
            res.status(500).json({ error: 'Internal Server Error', message: error.message });
        }
    });

    // GET /verifiable/presentation - Get exchange by ID in session
    diagencyRouter.get('/verifiable/presentation', async (req, res) => {
        try {
            // Check if session has dcRes
            if (!req.session.dcRes) {
                return res.status(400).json({
                    error: 'Bad Request',
                    message: 'No active session or exchange not initialized'
                });
            }

            // Get exchange ID from session
            const exchangeId = req.session.dcRes.json?.id || req.session.dcRes.data?.id;

            if (!exchangeId) {
                return res.status(400).json({
                    error: 'Bad Request',
                    message: 'Exchange ID not found in session'
                });
            }

            const dcReq = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            };

            const dcRes = await preCallDigitalCredsService(dcReq, res, `/v1.0/oidvc/vp/exchange/${exchangeId}`);

            // Update session with new response
            req.session.dcRes = dcRes;

            // Send response
            sendDigitalCredsResult(res, dcRes);
        } catch (error) {
            console.error('Error in GET /verifiable/presentation:', error);
            res.status(500).json({ error: 'Internal Server Error', message: error.message });
        }
    });

    // GET /verifiable/presentation/vc - Get verification by ID in session
    diagencyRouter.get('/verifiable/presentation/vc', async (req, res) => {
        try {
            // Check if session has dcRes
            if (!req.session.dcRes) {
                return res.status(400).json({
                    error: 'Bad Request',
                    message: 'No active session or exchange not initialized'
                });
            }

            // Get exchange ID from session
            const exchangeId = req.session.dcRes.json?.id || req.session.dcRes.data?.id;

            if (!exchangeId) {
                return res.status(400).json({
                    error: 'Bad Request',
                    message: 'Exchange ID not found in session'
                });
            }

            const dcReq = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            };


            const dcRes = await preCallDigitalCredsService(dcReq, res, `/v1.0/diagency/verifications/${exchangeId}`);

            const resultToSend = {
                status: dcRes.status,
                headers: dcRes.headers,
            }

            if (dcRes.json) {
                resultToSend.json = {
                    attributes: dcRes.json?.oid4vp?.[0]?.decoded?.attributes,
                };
            }
            if (dcRes.data) {
                resultToSend.data = {
                    attributes: dcRes.data?.oid4vp?.[0]?.decoded?.attributes,
                };
            }

            // Send response (don't update session for vc endpoint)
            sendDigitalCredsResult(res, resultToSend);
        } catch (error) {
            console.error('Error in GET /verifiable/presentation/vc:', error);
            res.status(500).json({ error: 'Internal Server Error', message: error.message });
        }
    });

    // Handle all other paths with 403 Forbidden
    diagencyRouter.use((req, res) => {
        console.warn(`Blocked unauthorized ${sanitizeForLog(req.method)} request to ${sanitizeForLog(req.url)}`);
        res.status(403).json({
            error: 'Forbidden',
            message: 'Access to this endpoint is forbidden'
        });
    });

    app.use('/credentials', diagencyRouter);
}

// Made with Bob