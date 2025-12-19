# Deploying Aviothic Breast Cancer AI Platform on Render

This guide will walk you through deploying the Aviothic Breast Cancer AI Platform on Render.

## Prerequisites

1. A Render account (free tier available)
2. A MongoDB Atlas account (or another MongoDB provider)
3. GitHub account (for automatic deployments)

## Step 1: Prepare Your Repository

1. Fork or clone the Aviothic Breast Cancer AI Platform repository
2. Ensure your repository has the following structure:
   ```
   aviothic-breast-cancer-ai/
   ├── backend/
   │   ├── main.py
   │   ├── requirements.txt
   │   └── ...
   ├── frontend/
   │   ├── package.json
   │   └── ...
   └── ...
   ```

## Step 2: Set Up MongoDB

1. Sign up for MongoDB Atlas (free tier available)
2. Create a new cluster
3. Whitelist all IP addresses (0.0.0.0/0) for testing
4. Create a database user with read/write permissions
5. Note your MongoDB connection string

## Step 3: Deploy the Backend to Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: aviothic-backend
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `MONGO_URI`: Your MongoDB connection string
     - `MONGO_DB`: Your database name (e.g., aviothic_db)
     - `PYTHON_VERSION`: 3.9.7
     - `PORT`: 8000

5. Click "Create Web Service"

## Step 4: Deploy the Frontend to Render

1. In the Render Dashboard, click "New" and select "Static Site"
2. Connect your GitHub repository
3. Configure the service:
   - **Name**: aviothic-frontend
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `frontend/build`
   - **Environment Variables**:
     - `NODE_VERSION`: 16.13.0

4. Add routing configuration in `render.yaml`:
   ```yaml
   routes:
     - type: rewrite
       source: /api/:path*
       destination: https://YOUR_BACKEND_URL/api/:path*
   ```

5. Click "Create Static Site"

## Step 5: Configure Environment Variables

1. In your backend service settings, go to "Environment"
2. Add the following variables:
   - `MONGO_URI`: Your MongoDB connection string
   - `MONGO_DB`: Your database name
   - `SECRET_KEY`: A secure random string for JWT tokens

## Step 6: Set Up Automatic Deployments

1. In each service, go to "Settings"
2. Enable "Auto-Deploy" from the master branch
3. Optionally, configure deploy hooks for CI/CD

## Step 7: Test Your Deployment

1. Wait for the builds to complete (this may take 5-10 minutes)
2. Visit your frontend URL
3. Test the image upload and prediction functionality
4. Check that reports are generated correctly

## Troubleshooting

### Common Issues

1. **MongoDB Connection Errors**:
   - Ensure your MongoDB Atlas IP whitelist includes Render's IPs
   - Check that your credentials are correct

2. **Build Failures**:
   - Check the build logs in Render for specific error messages
   - Ensure all dependencies are listed in requirements.txt

3. **Runtime Errors**:
   - Check the application logs in Render
   - Verify environment variables are set correctly

### Monitoring

1. Use Render's built-in logging to monitor your application
2. Set up alerts for downtime or performance issues
3. Monitor MongoDB usage in Atlas dashboard

## Updating Your Deployment

1. Push changes to your GitHub repository
2. Render will automatically deploy if auto-deploy is enabled
3. Alternatively, trigger a manual deploy from the Render dashboard

## Scaling

1. Render automatically scales based on traffic
2. For heavy usage, consider upgrading to a paid plan
3. For the database, upgrade your MongoDB Atlas tier as needed

## Conclusion

Your Aviothic Breast Cancer AI Platform should now be deployed and accessible on Render. The platform provides advanced breast cancer detection capabilities through a user-friendly web interface.