# Deploying Aviothic Breast Cancer AI Platform on Vercel

This guide will walk you through deploying the frontend of the Aviothic Breast Cancer AI Platform on Vercel.

## Prerequisites

1. A Vercel account (free tier available)
2. A GitHub account
3. The backend deployed (see RENDER_DEPLOY.md for backend deployment)

## Step 1: Prepare Your Repository

1. Fork or clone the Aviothic Breast Cancer AI Platform repository
2. Ensure your repository has the following structure:
   ```
   aviothic-breast-cancer-ai/
   ├── frontend/
   │   ├── package.json
   │   ├── vercel.json
   │   └── ...
   └── ...
   ```

## Step 2: Deploy the Frontend to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your Git repository
4. Configure the project:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build and Output Settings**:
     - **Build Command**: `npm run build`
     - **Output Directory**: `build`
     - **Install Command**: `npm install`

5. Add environment variables:
   - `REACT_APP_API_URL`: Your backend URL (e.g., https://your-backend.onrender.com)

6. Click "Deploy"

## Step 3: Configure API Proxy (Optional)

To avoid CORS issues, you can configure Vercel to proxy API requests to your backend:

1. Create or update `vercel.json` in the frontend directory:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/:path*",
         "destination": "https://your-backend-url.onrender.com/:path*"
       }
     ]
   }
   ```

2. Replace `your-backend-url.onrender.com` with your actual backend URL

## Step 4: Environment Variables

Add the following environment variables in your Vercel project settings:

1. Go to your project settings in Vercel
2. Navigate to "Environment Variables"
3. Add:
   - `REACT_APP_API_URL`: Your backend URL

## Step 5: Custom Domain (Optional)

1. In your Vercel project, go to "Settings" > "Domains"
2. Add your custom domain
3. Follow Vercel's instructions to configure DNS

## Step 6: Test Your Deployment

1. Wait for the deployment to complete
2. Visit your Vercel URL
3. Test the image upload and prediction functionality
4. Check that reports are generated correctly

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Ensure your backend allows requests from your Vercel domain
   - Configure API proxy in `vercel.json`

2. **Build Failures**:
   - Check the build logs in Vercel for specific error messages
   - Ensure all dependencies are listed in package.json

3. **Runtime Errors**:
   - Check the application logs in Vercel
   - Verify environment variables are set correctly

### Monitoring

1. Use Vercel's analytics to monitor your application performance
2. Set up alerts for downtime or performance issues
3. Monitor usage and bandwidth

## Updating Your Deployment

1. Push changes to your GitHub repository
2. Vercel will automatically deploy if auto-deploy is enabled
3. Alternatively, trigger a manual deploy from the Vercel dashboard

## Conclusion

Your Aviothic Breast Cancer AI Platform frontend should now be deployed and accessible on Vercel. Combined with your backend deployment, the complete platform provides advanced breast cancer detection capabilities through a user-friendly web interface.