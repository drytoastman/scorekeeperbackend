const path = require('path');
module.exports = {
  mode: 'production',
  entry: {
    live: [ './src/components/user-panel.js', './src/components/announcer-panel.js' ]
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

