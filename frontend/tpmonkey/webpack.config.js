const path = require("path");
const webpack = require('webpack');

module.exports = {
    // 入口
    entry: {
        main: "./src/main.js",
    },
    mode: "development", 
    output: {
        filename: "[name].js",
        // 导出到dist目录下
        path: path.resolve(__dirname, "./dist")
    },
    optimization: {
        minimize: false
    },
    plugins: [
        new webpack.DefinePlugin({
            'BASE_URL': JSON.stringify('http://127.0.0.1:5018'),
            'GLS_HOST': JSON.stringify('http://127.0.0.1:5001')
        })
    ]
}