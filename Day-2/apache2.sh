#!/bin/bash -xe

# Update apt and install apache
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y apache2

# Ensure apache will start and is enabled
systemctl enable --now apache2

# Create the web root index with the zoom in/out animation
cat > /var/www/html/index.html <<'HTML'
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Welcome to server1</title>
  <style>
    /* Full-screen, black background */
    html,body {
      height: 100%;
      margin: 0;
      background: #000;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    /* Centering container */
    .center {
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }

    /* Text styling */
    .message {
      color: #fff;
      font-weight: 600;
      text-transform: lowercase;
      letter-spacing: 1px;
      font-size: clamp(28px, 6vw, 72px);
      transform-origin: center center;
      will-change: transform, opacity;
      /* soft glowing effect */
      text-shadow: 0 4px 18px rgba(255,255,255,0.06), 0 1px 3px rgba(255,255,255,0.04);
      animation: zoomInOut 3.2s ease-in-out infinite;
    }

    /* Zoom in/out keyframes */
    @keyframes zoomInOut {
      0% {
        transform: scale(0.88);
        opacity: 0.85;
      }
      50% {
        transform: scale(1.12);
        opacity: 1;
      }
      100% {
        transform: scale(0.88);
        opacity: 0.85;
      }
    }

    /* small screens tweak */
    @media (max-width: 420px) {
      .message { font-size: 24px; }
    }
  </style>
</head>
<body>
  <div class="center">
    <div class="message">welcome to server1</div>
  </div>
</body>
</html>
HTML

# Fix ownership/permissions just in case
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html

# Restart apache to ensure the new page is active
systemctl restart apache2

# Done
echo "User-data finished: apache installed and index.html created"