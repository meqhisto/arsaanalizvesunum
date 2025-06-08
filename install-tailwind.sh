#!/bin/bash

# Install Tailwind CSS and dependencies
echo "Installing Tailwind CSS and dependencies..."

# Install npm dependencies
npm install

# Build the project with Tailwind CSS
echo "Building project with Tailwind CSS..."
npm run build

echo "Tailwind CSS installation and build complete!"
echo ""
echo "Next steps:"
echo "1. Run 'npm run dev' for development mode"
echo "2. Run 'npm run build' for production build"
echo "3. Start your Flask application"
