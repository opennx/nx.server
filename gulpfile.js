'use strict';

// Gulp && plugins
var gulp = require('gulp');

var cleanCSS = require('gulp-clean-css');
var sass = require('gulp-sass');
var concat = require('gulp-concat');
var minify = require('gulp-minify');


var vendor_js = [
    './node_modules/jquery/dist/jquery.js',
//    './node_modules/vue/dist/vue.js',
    './node_modules/bootstrap-sass/assets/javascripts/bootstrap.js',
    './node_modules/bootstrap-material-design/scripts/material.js',
    './node_modules/bootstrap-material-design/scripts/ripples.js'
];


gulp.task('vendor', function() {

	// javascripts
    gulp.src(vendor_js)
        .pipe(concat('vendor.js'))
        .pipe(minify({
                ext:{
                    src:'.js',
                    min:'.min.js'
                },
                compress: {
                    properties: false
                },
            }))
        .pipe(gulp.dest('./hub/static/js'));

    // bootstrap-sass
    gulp.src('./node_modules/bootstrap-sass/assets/stylesheets/**/*.scss')
        .pipe(gulp.dest('./hub/src/sass/vendor'));
    gulp.src('./node_modules/bootstrap-sass/assets/fonts/bootstrap/*.{ttf,svg,eot,woff,woff2}')
        .pipe(gulp.dest('./hub/src/static/fonts/bootstrap'));

	// font awesome
    gulp.src('./node_modules/font-awesome/scss/*.scss')
        .pipe(gulp.dest('./hub/src/sass/vendor/font-awesome'));
    gulp.src('./node_modules/font-awesome/fonts/*.{ttf,svg,eot,woff,woff2,otf}')
        .pipe(gulp.dest('./hub/src/static/fonts'));

    // bootstrap-material-design
    gulp.src('./node_modules/bootstrap-material-design/sass/**/*.scss')
        .pipe(gulp.dest('./hub/src/sass/vendor'));

});


gulp.task('sass', function() {
    gulp.src('./hub/src/sass/main.scss')
        .pipe(sass.sync().on('error', sass.logError))
        .pipe(cleanCSS())
        .pipe(gulp.dest('./hub/static/css'));
});


gulp.task('js', function() {
    gulp.src('./hub/src/js/*.js')
        .pipe(minify({
                ext:{
                    src:'.js',
                    min:'.min.js'
                },
                compress: {
                    properties: false
                },
            }))
        .pipe(gulp.dest('./hub/static/js'));
});


