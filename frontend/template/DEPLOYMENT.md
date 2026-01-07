# 🚀 Deployment Guide - Template Manager

## Overview
This guide covers deploying the Template Manager frontend to various platforms.

## 📋 Pre-Deployment Checklist

- [ ] Backend API is deployed and accessible
- [ ] Database migrations are applied
- [ ] CORS is configured on backend
- [ ] Environment variables are set
- [ ] App builds successfully (`npm run build`)
- [ ] App tested locally

## 🏗️ Build for Production

```bash
cd /Users/abskchsk/Documents/govindjis/wa-app/frontend/template
npm run build
```

This creates an optimized production build in the `build/` folder.

## Deployment Options

### Option 1: AWS S3 + CloudFront (Recommended)

#### Step 1: Build the app
```bash
npm run build
```

#### Step 2: Create S3 bucket
```bash
aws s3 mb s3://template-manager-govindjis
aws s3 website s3://template-manager-govindjis --index-document index.html
```

#### Step 3: Upload build files
```bash
cd build
aws s3 sync . s3://template-manager-govindjis --acl public-read
```

#### Step 4: Configure CloudFront (optional)
- Create CloudFront distribution
- Point to S3 bucket
- Enable HTTPS
- Set custom domain

**Pros**: Highly scalable, fast, cost-effective  
**Cons**: Requires AWS account

---

### Option 2: Netlify (Easiest)

#### Step 1: Install Netlify CLI
```bash
npm install -g netlify-cli
```

#### Step 2: Deploy
```bash
cd /Users/abskchsk/Documents/govindjis/wa-app/frontend/template
netlify deploy --prod
```

Or use Netlify web UI:
1. Connect GitHub repository
2. Set build command: `npm run build`
3. Set publish directory: `build`
4. Deploy!

**Pros**: Zero config, automatic deployments, free tier  
**Cons**: Limited to Netlify ecosystem

---

### Option 3: Vercel

#### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

#### Step 2: Deploy
```bash
cd /Users/abskchsk/Documents/govindjis/wa-app/frontend/template
vercel --prod
```

Or use Vercel web UI:
1. Import GitHub repository
2. Auto-detects React app
3. Deploy!

**Pros**: Zero config, great performance, free tier  
**Cons**: Limited to Vercel ecosystem

---

### Option 4: AWS Amplify

#### Step 1: Install Amplify CLI
```bash
npm install -g @aws-amplify/cli
amplify configure
```

#### Step 2: Initialize Amplify
```bash
cd /Users/abskchsk/Documents/govindjis/wa-app/frontend/template
amplify init
amplify add hosting
```

#### Step 3: Deploy
```bash
amplify publish
```

**Pros**: Integrated with AWS backend, CI/CD  
**Cons**: More complex setup

---

### Option 5: Docker + AWS ECS/App Runner

#### Create Dockerfile
```dockerfile
# Build stage
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Create nginx.conf
```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass https://2hdfnnus3x.us-east-1.awsapprunner.com;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### Build & Deploy
```bash
docker build -t template-manager .
docker tag template-manager:latest <ECR_URI>:latest
docker push <ECR_URI>:latest
```

Then deploy to ECS or App Runner.

**Pros**: Full control, portable  
**Cons**: More complex, requires container knowledge

---

## Environment Configuration

### Development
```bash
REACT_APP_API_URL=http://localhost:8000
```

### Staging
```bash
REACT_APP_API_URL=https://staging-api.example.com
```

### Production
```bash
REACT_APP_API_URL=https://2hdfnnus3x.us-east-1.awsapprunner.com
```

## Post-Deployment Testing

### 1. Health Check
Visit: `https://your-domain.com`

### 2. API Connectivity
Open browser console and check for:
- ✅ API requests to backend
- ✅ Successful responses
- ❌ No CORS errors

### 3. Functionality Test
- [ ] Load template list
- [ ] Create new template
- [ ] Edit template
- [ ] Delete template

### 4. Browser Testing
Test on:
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Mobile browsers

## Performance Optimization

### Code Splitting
React Scripts automatically handles code splitting.

### Caching
Configure CloudFront or CDN cache headers:
```
index.html: no-cache
*.js, *.css: cache for 1 year
```

### Compression
Enable Gzip/Brotli compression on server.

### Bundle Analysis
```bash
npm run build
npx source-map-explorer 'build/static/js/*.js'
```

## Monitoring & Analytics

### Add Google Analytics (optional)
```javascript
// In public/index.html
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

### Error Tracking (optional)
Consider adding Sentry or similar for error tracking.

## Security Considerations

### HTTPS Only
Always use HTTPS in production.

### CSP Headers
Configure Content Security Policy:
```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';
```

### API Rate Limiting
Ensure backend has rate limiting configured.

## Rollback Strategy

### Keep previous builds
```bash
aws s3 sync build/ s3://bucket/releases/$(date +%Y%m%d-%H%M%S)/
```

### Quick rollback
```bash
aws s3 sync s3://bucket/releases/PREVIOUS_VERSION/ s3://bucket/current/
```

## Cost Estimates

### AWS S3 + CloudFront
- S3 storage: ~$0.50/month
- CloudFront: ~$1-5/month (low traffic)
- Total: ~$2-6/month

### Netlify/Vercel
- Free tier: $0/month
- Pro tier: $19-20/month

### AWS Amplify
- Build minutes: Free tier available
- Hosting: ~$0.15/GB transferred
- Total: ~$2-10/month

## Recommended Setup for Production

1. **Frontend**: AWS S3 + CloudFront
2. **Domain**: Route 53 or your DNS provider
3. **SSL**: AWS Certificate Manager (free)
4. **CI/CD**: GitHub Actions
5. **Monitoring**: CloudWatch

## Continuous Deployment (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to S3

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: npm ci
      working-directory: frontend/template
    
    - name: Build
      run: npm run build
      working-directory: frontend/template
      env:
        REACT_APP_API_URL: ${{ secrets.API_URL }}
    
    - name: Deploy to S3
      uses: jakejarvis/s3-sync-action@master
      with:
        args: --delete
      env:
        AWS_S3_BUCKET: ${{ secrets.AWS_S3_BUCKET }}
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        SOURCE_DIR: 'frontend/template/build'
```

## Support & Troubleshooting

### Common Issues

**Build fails**
- Check Node.js version (requires 14+)
- Clear cache: `rm -rf node_modules package-lock.json && npm install`

**Blank page after deployment**
- Check browser console for errors
- Verify API URL in .env
- Check CORS configuration

**API requests fail**
- Verify backend is running
- Check CORS headers
- Verify API URL is correct

## Summary

For your use case, I recommend:
1. **Quick testing**: Use Netlify (fastest, zero config)
2. **Production**: AWS S3 + CloudFront (best performance, low cost)
3. **Enterprise**: Docker + AWS App Runner (full control)

Choose based on your needs and infrastructure!
