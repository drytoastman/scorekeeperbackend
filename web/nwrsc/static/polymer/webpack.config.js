const path = require('path');
module.exports = {
  entry: {
    live: [ './src/components/user-panel.js', './src/components/announcer-panel.js' ]
  },

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
