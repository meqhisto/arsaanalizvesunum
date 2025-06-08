const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';

  return {
    entry: './frontend/src/js/app.js',

    output: {
      path: path.resolve(__dirname, 'frontend/dist'),
      filename: isProduction ? '[name].[contenthash].js' : '[name].js',
      clean: true,
      publicPath: '/'
    },

    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: ['@babel/preset-env']
            }
          }
        },
        {
          test: /\.scss$/,
          use: [
            isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
            'css-loader',
            'postcss-loader',
            'sass-loader'
          ]
        },
        {
          test: /\.css$/,
          use: [
            isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
            'css-loader',
            'postcss-loader'
          ]
        },
        {
          test: /\.(png|svg|jpg|jpeg|gif)$/i,
          type: 'asset/resource',
          generator: {
            filename: 'images/[name].[hash][ext]'
          }
        },
        {
          test: /\.(woff|woff2|eot|ttf|otf)$/i,
          type: 'asset/resource',
          generator: {
            filename: 'fonts/[name].[hash][ext]'
          }
        }
      ]
    },

    plugins: [
      new HtmlWebpackPlugin({
        template: './frontend/src/index.html',
        filename: 'index.html',
        inject: 'body'
      }),
      ...(isProduction ? [
        new MiniCssExtractPlugin({
          filename: '[name].[contenthash].css'
        })
      ] : [])
    ],

    devServer: {
      static: {
        directory: path.join(__dirname, 'frontend/dist'),
      },
      compress: true,
      port: 3001,
      hot: true,
      historyApiFallback: true,
      proxy: {
        '/api': {
          target: 'http://localhost:5000',
          changeOrigin: true,
          secure: false
        },
        '/static': {
          target: 'http://localhost:5000',
          changeOrigin: true,
          secure: false
        }
      },
      client: {
        overlay: {
          errors: true,
          warnings: false
        }
      }
    },

    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
          }
        }
      }
    },

    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'frontend/src/js'),
        '@css': path.resolve(__dirname, 'frontend/src/css'),
        '@components': path.resolve(__dirname, 'frontend/src/js/components'),
        '@pages': path.resolve(__dirname, 'frontend/src/js/pages'),
        '@utils': path.resolve(__dirname, 'frontend/src/js/utils'),
        '@api': path.resolve(__dirname, 'frontend/src/js/api')
      }
    },

    devtool: isProduction ? 'source-map' : 'eval-source-map'
  };
};
