/**
 * API Service for making requests to the backend
 */
import { reliableFetch } from '../reliableFetch';

class BankApiService {
  /**
   * Process request body based on its type
   * @param body The request body
   * @param headers Request headers
   * @returns Processed body ready for fetch
   */
  private processRequestBody(body: any, headers?: Record<string, string>): any {
    if (body instanceof URLSearchParams) {
      return body;
    }
    
    if (typeof body === 'string') {
      // If the content type is JSON, ensure the body is valid JSON
      const contentType = headers?.['Content-Type'] || '';
      if (contentType.includes('application/json')) {
        try {
          JSON.parse(body); // Validate JSON
        } catch (e: any) {
          throw new Error('Invalid JSON in request body');
        }
      }
      return body;
    }
    
    // Otherwise, assume it's JSON
    return JSON.stringify(body);
  }

  /**
   * Make a request to the API
   * @param path The API path
   * @param options Request options
   * @returns The response data
   */
  async request<T = any>(path: string, options: {
    method?: string;
    headers?: Record<string, string>;
    body?: any;
  } = {}): Promise<T> {
    try {
      // Create the request URL - use relative paths for the proxy
      const url = path.startsWith('/') ? path : `/${path}`;
      
      // Prepare fetch options
      const fetchOptions: RequestInit = {
        method: options.method || 'GET',
        headers: options.headers || {},
        redirect: 'follow',
        credentials: 'include' // Include cookies for session authentication
      };

      // Handle body if present
      if (options.body) {
        fetchOptions.body = this.processRequestBody(options.body, options.headers);
      }
      
      // Make the request using reliable fetch with retry logic
      const response = await reliableFetch(url, fetchOptions);
      
      // Check if the response is OK
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }
      
      // Parse the response as JSON
      try {
        const data = await response.json();
        return data;
      } catch (jsonError: any) {
        throw new Error(`Failed to parse API response as JSON: ${jsonError.message || 'Unknown error'}`);
      }
    } catch (error: any) {
      throw error;
    }
  }

  /**
   * Make an authenticated request to the API
   * The proxy will automatically add the authentication token
   * @param path The API path
   * @param options Request options
   * @returns The response data
   */
  async unauthenticatedRequest<T = any>(path: string, options: {
    method?: string;
    headers?: Record<string, string>;
    body?: any;
  } = {}): Promise<T> {
    try {
      // Make the request - the proxy will handle authentication
      return this.request<T>(path, options);
    } catch (error: any) {
      throw error;
    }
  }

  /**
   * Make an authenticated request to the API and return the raw response
   * Useful for non-JSON responses like images/blobs
   * The proxy will automatically add the authentication token
   * @param path The API path
   * @param options Request options
   * @returns The raw Response object
   */
  async authenticatedRawRequest(path: string, options: {
    method?: string;
    headers?: Record<string, string>;
    body?: any;
    responseType?: string;
  } = {}): Promise<Response> {
    try {
      // Create the request URL - use relative paths for the proxy
      const url = path.startsWith('/') ? path : `/${path}`;
      
      // Prepare fetch options
      const fetchOptions: RequestInit = {
        method: options.method || 'GET',
        headers: options.headers || {},
        redirect: 'follow',
        credentials: 'include' // Include cookies for session authentication
      };

      // Handle different body formats
      if (options.body) {
        if (options.body instanceof URLSearchParams) {
          fetchOptions.body = options.body;
        } else if (typeof options.body === 'string') {
          fetchOptions.body = options.body;
        } else {
          fetchOptions.body = JSON.stringify(options.body);
        }
      }

      // Make the request using reliable fetch - the proxy will handle authentication
      const response = await reliableFetch(url, fetchOptions);
      
      // Check if the response is OK
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }
      
      // Return the raw response
      return response;
    } catch (error: any) {
      throw error;
    }
  }
}

// Create a singleton instance
const diagencyApiService = new BankApiService();

export default diagencyApiService;

// Made with Bob
