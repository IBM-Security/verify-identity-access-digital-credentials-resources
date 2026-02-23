/**
 * setupProxy.mjs
 * Development proxy handling external requests + OIDC auth (IBM Verify) using openid-client v6+
 */

import express from 'express';
import bodyParser from 'body-parser';
import * as client from 'openid-client';
import session from 'express-session';
import crypto from 'crypto';
import { reliableFetch, reliableFetchGet, reliableFetchPost } from './reliableFetch.mjs';
import * as uuid from 'uuid';

/**
 * Sanitize user input for logging to prevent log forging attacks
 * Removes newlines, carriage returns, and other control characters
 * @param {string} input - The input to sanitize
 * @returns {string} Sanitized input safe for logging
 */
function sanitizeForLog(input) {
    if (typeof input !== 'string') {
        input = String(input);
    }
    // Replace newlines, carriage returns, and other control characters
    return input.replace(/[\r\n\t\x00-\x1F\x7F]/g, ' ').trim();
}

// --- Environment / config ---
const diagencyAccountUrl = process.env.REACT_APP_ACCOUNT_URL || '';
const tokenUrl = process.env.REACT_APP_TOKEN_ENDPOINT || '';
const w3Root = process.env.REACT_APP_W3_ROOT || '';

const dmvAgentId = process.env.REACT_APP_DMV_AGENT_ID || '';
const dmvAgentPassword = process.env.REACT_APP_DMV_AGENT_PASSWORD || '';

const clientId = process.env.REACT_APP_CLIENT_ID || '';
const clientSecret = process.env.REACT_APP_CLIENT_SECRET || '';
const redirectUri = process.env.REACT_APP_DMV_REDIRECT_URL || '';

// --- Token storage ---
const tokenStorage = { accessToken: '', expiresAt: 0 };

// --- Session configuration ---
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
    name: 'dmv.session.id' // Custom session name
};

// --- Authentication middleware ---
function requireAuth(req, res, next) {
    if (!req.session?.user?.authenticated) {
        return res.status(401).json({
            error: 'Unauthorized',
            message: 'Authentication required'
        });
    }
    next();
}

// Check token expiry and session validity
function requireValidSession(req, res, next) {
    console.log('[DMV-AUTH] Checking session validity');
    console.log('[DMV-AUTH] Session exists:', !!req.session);
    console.log('[DMV-AUTH] User in session:', !!req.session?.user);
    console.log('[DMV-AUTH] User authenticated:', req.session?.user?.authenticated);

    if (!req.session?.user?.authenticated) {
        console.log('[DMV-AUTH] Authentication required - no valid session found');
        return res.status(401).json({
            error: 'Unauthorized',
            message: 'Authentication required'
        });
    }

    // Check if tokens are expired
    const now = Date.now();
    if (req.session.user.tokenExpiresAt && req.session.user.tokenExpiresAt < now) {
        console.log('[DMV-AUTH] Session expired');
        req.session.destroy();
        return res.status(401).json({
            error: 'Session Expired',
            message: 'Please login again'
        });
    }

    console.log('[DMV-AUTH] Session valid, proceeding');
    next();
}

// --- Helper to forward requests ---
async function forwardRequest(req, res, targetUrl, options = {}) {
    try {
        console.log(`[DMV-PROXY] Forwarding ${sanitizeForLog(req.method)} request to ${sanitizeForLog(targetUrl)}`);
        const isImageRequest = req.headers.accept?.includes('image/');
        const fetchOptions = {
            method: req.method,
            headers: { ...req.headers, ...(options.headers || {}), host: new URL(targetUrl).host },
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
                console.log(`[DMV-PROXY] Request body: ${sanitizeForLog(JSON.stringify(req.body).substring(0, 200))}`);
            }
        }

        const response = await reliableFetch(targetUrl, fetchOptions, {
            timeout: options.timeout ?? 10000,
            onRetry: (attempt, error) => {
                console.log(`[DMV-PROXY] Retrying request to ${targetUrl}, attempt ${attempt}. Error: ${error.message}`);
            }
        });

        console.log(`[DMV-PROXY] Response status: ${response.status}, Content-Type: ${response.headers.get('content-type')}`);

        res.status(response.status);
        response.headers.forEach((value, key) => {
            // Skip transfer-encoding and content-encoding headers
            // content-encoding is handled by fetch automatically, so we shouldn't forward it
            // as the body is already decompressed
            if (key !== 'transfer-encoding' && key !== 'content-encoding') {
                res.setHeader(key, value);
            }
        });

        if (options.followRedirects && response.headers.get('location')) return res.redirect(response.headers.get('location'));

        // Check content type to determine how to handle the response
        const contentType = response.headers.get('content-type') || '';

        if (options.jsonResponse || contentType.includes('application/json')) {
            const data = await response.json();
            console.log(`[DMV-PROXY] Sending JSON response: ${JSON.stringify(data).substring(0, 200)}`);
            res.json(data);
        } else if (isImageRequest || contentType.includes('image/')) {
            const arrayBuffer = await response.arrayBuffer();
            console.log(`[DMV-PROXY] Sending image response, size: ${arrayBuffer.byteLength} bytes`);
            res.send(Buffer.from(arrayBuffer));
        } else {
            const text = await response.text();
            console.log(`[DMV-PROXY] Sending text response: ${text.substring(0, 200)}`);
            res.send(text);
        }
    } catch (error) {
        console.error(`[DMV-PROXY] Error forwarding request to ${sanitizeForLog(targetUrl)}:`, error);
        handleRequestError(error, res, options);
    }
}

function handleRequestError(error, res, options = {}) {
    // For fetch errors, we don't have a response object
    console.error(`[DMV-PROXY] Request error:`, error);
    res.status(504).json({
        error: 'Gateway Timeout',
        message: error.message || 'No response received from server'
    });
}

// --- DMV Token Helper ---
async function getOrRefreshDmvToken() {
    if (tokenStorage.accessToken && tokenStorage.expiresAt > Date.now()) return tokenStorage.accessToken;

    const formBody = new URLSearchParams({
        client_id: dmvAgentId,
        client_secret: dmvAgentPassword,
        grant_type: 'client_credentials'
    });

    const response = await reliableFetchPost(tokenUrl, formBody, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', Accept: 'application/json' }
    }, {
        timeout: 30000,
        onRetry: (attempt, error) => {
            console.log(`[DMV-TOKEN] Retrying token request, attempt ${attempt}. Error: ${error.message}`);
        }
    });

    if (!response.ok) {
        throw new Error(`Token request failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    tokenStorage.accessToken = data.access_token;
    tokenStorage.expiresAt = Date.now() + (data.expires_in * 1000) - 60000;
    return tokenStorage.accessToken;
}

// --- OIDC Setup ---
let oidcClient = null;
const authParams = new Map();

async function loadOidcClient() {
    if (!oidcClient) {
        if (!clientId) throw new Error('Client ID not defined (REACT_APP_CLIENT_ID)');
        if (!w3Root) throw new Error('W3 root not defined (REACT_APP_W3_ROOT)');

        try {
            // Create a URL object for the server's issuer identifier with the correct path
            const issuerUrl = new URL(w3Root + '/oauth2');
            const configUrl = new URL(w3Root + '/oauth2/.well-known/openid-configuration');
            console.log(`Attempting to discover OIDC configuration from: ${configUrl.href}`);

            // Use the discovery method with the correct configuration URL and our reliable fetch
            const config = await client.discovery(
                issuerUrl,
                clientId,
                clientSecret,
                {
                    discoveryEndpoint: configUrl,
                    [client.customFetch]: reliableFetch
                }
            );

            oidcClient = config;
            console.log('OIDC client successfully initialized');
        } catch (error) {
            console.error('Failed to initialize OIDC client:', error);
            throw new Error(`OIDC discovery failed: ${error.message}. Please check that REACT_APP_W3_ROOT is correctly configured.`);
        }
    }
    return oidcClient;
}

// --- Main Export ---
export default function setupRoutes(app) {
    // Trust proxy - required when behind a reverse proxy (like in production)
    // This ensures secure cookies work correctly with HTTPS termination at the proxy
    app.set('trust proxy', 1);

    app.use(bodyParser.json());
    app.use(bodyParser.urlencoded({ extended: true }));

    // Add session middleware
    app.use(session(sessionConfig));

    // --- Auth routes ---
    const authRouter = express.Router();

    authRouter.get('/login', async (req, res) => {
        try {
            const config = await loadOidcClient();

            // Generate PKCE code verifier and challenge
            const code_verifier = client.randomPKCECodeVerifier();
            const code_challenge = await client.calculatePKCECodeChallenge(code_verifier);
            const state = client.randomState();

            // Store the code verifier and state for later use
            authParams.set(state, { code_verifier, createdAt: Date.now() });

            // Build the authorization URL with parameters
            const parameters = {
                redirect_uri: redirectUri,
                scope: 'openid profile email',
                response_type: 'code',
                code_challenge,
                code_challenge_method: 'S256',
                state
            };

            const redirectTo = client.buildAuthorizationUrl(config, parameters);

            res.json({ authUrl: redirectTo.href, state });
        } catch (err) {
            console.error('Error generating auth URL:', err);
            res.status(500).json({ error: 'Failed to generate authorization URL', details: err.message });
        }
    });

    authRouter.post('/callback', async (req, res) => {
        try {
            const config = await loadOidcClient();
            const { code, state } = req.body;
            if (!code || !state) return res.status(400).json({ error: 'Missing code or state' });

            const params = authParams.get(state);
            if (!params) return res.status(400).json({ error: 'Invalid or expired state' });

            // Manually construct the token request
            const tokenEndpoint = new URL(`${w3Root}/oauth2/token`);
            const tokenParams = new URLSearchParams({
                grant_type: 'authorization_code',
                code: code,
                redirect_uri: redirectUri,
                client_id: clientId,
                client_secret: clientSecret,
                code_verifier: params.code_verifier
            });

            const tokenResponse = await reliableFetchPost(tokenEndpoint.href, tokenParams, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            }, {
                onRetry: (attempt, error) => {
                    console.log(`[DMV-OIDC] Retrying OIDC token exchange, attempt ${attempt}. Error: ${error.message}`);
                }
            });

            if (!tokenResponse.ok) {
                throw new Error(`Token exchange failed: ${tokenResponse.status} ${tokenResponse.statusText}`);
            }

            const tokens = await tokenResponse.json();

            authParams.delete(state);

            // Fetch user info if needed
            let userInfo = {};
            try {
                const userInfoEndpoint = new URL(`${w3Root}/oauth2/userinfo`);

                const userInfoResponse = await reliableFetchGet(userInfoEndpoint.href, {
                    headers: {
                        'Authorization': `Bearer ${tokens.access_token}`
                    }
                }, {
                    onRetry: (attempt, error) => {
                        console.log(`[DMV-OIDC] Retrying userinfo request, attempt ${attempt}. Error: ${error.message}`);
                    }
                });

                if (userInfoResponse.ok) {
                    userInfo = await userInfoResponse.json();
                } else {
                    throw new Error(`Userinfo request failed: ${userInfoResponse.status}`);
                }
            } catch (e) {
                console.error('Userinfo error:', e);
                // Continue even if userinfo fails
            }

            // Establish authenticated session
            req.session.user = {
                authenticated: true,
                userInfo,
                tokens: {
                    access_token: tokens.access_token,
                    id_token: tokens.id_token,
                    refresh_token: tokens.refresh_token
                },
                tokenExpiresAt: tokens.expires_in ? Date.now() + (tokens.expires_in * 1000) : null,
                loginTime: Date.now()
            };

            // Return success without exposing access tokens
            res.json({
                success: true,
                userInfo: {
                    name: userInfo.name,
                    given_name: userInfo.given_name,
                    family_name: userInfo.family_name,
                    email: userInfo.email,
                },
                message: 'Authentication successful'
            });
        } catch (err) {
            console.error('Error in callback:', err);
            res.status(500).json({ error: 'Authentication failed', details: err.message });
        }
    });

    // Check session status
    authRouter.get('/status', (req, res) => {
        if (req.session?.user?.authenticated) {
            res.json({
                authenticated: true,
                user: req.session.user.userInfo,
                loginTime: req.session.user.loginTime
            });
        } else {
            res.json({ authenticated: false });
        }
    });

    // Enhanced logout
    authRouter.post('/logout', async (req, res) => {
        try {
            let logoutUrl = null;

            // If we have an ID token in session, create logout URL
            if (req.session?.user?.tokens?.id_token) {
                const client = await loadOidcClient();
                logoutUrl = client.endSessionUrl({
                    id_token_hint: req.session.user.tokens.id_token,
                    post_logout_redirect_uri: redirectUri || `${w3Root}/`
                });
            }

            // Destroy session
            req.session.destroy((err) => {
                if (err) {
                    console.error('Session destruction error:', err);
                }
            });

            res.json({
                success: true,
                logoutUrl: logoutUrl
            });
        } catch (err) {
            console.error('Logout error:', err);
            res.json({ success: true });
        }
    });

    app.use('/auth', authRouter);

    // Helper function to forward authenticated requests to diagency
    async function forwardAuthenticatedRequest(req, res, path) {
        try {
            console.log(`[DMV-DIAGENCY] Forwarding authenticated request to path: ${sanitizeForLog(path)}`);
            const targetUrl = `${diagencyAccountUrl}${path}`;
            const token = await getOrRefreshDmvToken();
            console.log(`[DMV-DIAGENCY] Using token: ${token.substring(0, 20)}...`);
            const headers = { ...req.headers, authorization: `Bearer ${token}` };
            await forwardRequest(req, res, targetUrl, { headers, timeout: 30000 });
        } catch (err) {
            console.error('[DMV-DIAGENCY] Request error:', err.message, err.stack);
            res.status(500).json({ error: 'Failed to process request', details: err.message });
        }
    }

    // --- Diagency proxy with specific allowed paths ---
    const diagencyRouter = express.Router();

    // Apply authentication middleware to all diagency routes
    diagencyRouter.use(requireValidSession);

    // POST /v1.0/oidvc/vci/offers - Create credential offers
    diagencyRouter.post('/offers', (req, res) => {
        console.log('[DMV-DIAGENCY] POST /credentials/offers called');
        forwardAuthenticatedRequest(req, res, '/v1.0/oidvc/vci/offers');
    });

    // GET /v1.0/oidvc/vci/offers/:id - Get offer by ID (for status or QR code)
    diagencyRouter.get('/offers/:id', (req, res) => {
        const id = req.params.id;
        if (uuid.validate(id)) {
            console.log(`[DMV-DIAGENCY] GET /credentials/offers/${sanitizeForLog(id)} called`);
            forwardAuthenticatedRequest(req, res, `/v1.0/oidvc/vci/offers/${id}`);
        } else {
            console.warn(`Blocked bad UUID in offer GET endpoint.`); // Forbidden to be consistent with other paths below
            res.status(400).json({
                error: 'Forbidden',
                message: 'Access to this endpoint is forbidden'
            });
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
