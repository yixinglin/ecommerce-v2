const path = require("path");
const webpack = require('webpack');

module.exports = {
    // 入口
    entry: {
        main: "./src/main.js",
    },
    mode: "production", 
    output: {
        filename: "[name].js",
        // 导出到dist目录下
        path: path.resolve(__dirname, "./dist")
    },
    optimization: {
        minimize: true
    },
    plugins: [
        new webpack.DefinePlugin({
            'BASE_URL': JSON.stringify('http://192.168.8.95:5018'),
            'GLS_HOST': JSON.stringify('http://gls.dev.hansagt-trade.com')
        })
    ]
}