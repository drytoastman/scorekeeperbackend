const path = require('path');
module.exports = {
  mode: 'development',
  entry: {
    live: './src/components/live-panel.js',
    announcer: './src/components/announcer-panel.js',
  },
  //devtool: 'inline-source-map',

  optimization: {
    splitChunks: {
      chunks: 'all'
    }
  },

  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'dist'),
  },
};

