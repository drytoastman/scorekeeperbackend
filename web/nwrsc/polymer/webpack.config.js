const path = require('path');
module.exports = {
  mode: 'development',
  entry: path.resolve(__dirname, 'src/components/live-panel.js'),
  devtool: 'inline-source-map',

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

