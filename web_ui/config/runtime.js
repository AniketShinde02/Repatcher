/**
 * Centralized runtime configuration for Next.js frontend.
 * Consolidates all environment variables and external service locations.
 */

export const config = {
    backendUrl: process.env.BACKEND_URL || 'http://127.0.0.1:7860',
    marketingUrl: process.env.MARKETING_URL || 'http://127.0.0.1:3003',
    appUrl: process.env.APP_URL || 'http://127.0.0.1:3000',
    environment: process.env.NODE_ENV || 'development',
};
