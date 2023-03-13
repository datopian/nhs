const { src, watch, dest } = require("gulp");
const sass = require("gulp-sass")(require("sass"));
const if_ = require("gulp-if");
const sourcemaps = require("gulp-sourcemaps");
const cleanCss = require("gulp-clean-css");
const rename = require("gulp-rename");


const with_sourcemaps = () => !!process.env.DEBUG;

const build = () =>
  src([
    __dirname + "/ckanext/nhs/fanstatic/sass/nhs.scss"
  ])
  .pipe(if_(with_sourcemaps(), sourcemaps.init()))
  .pipe(sass({ outputStyle: 'expanded' }).on('error', sass.logError))
  .pipe(if_(with_sourcemaps(), sourcemaps.write()))
  .pipe(dest(__dirname + "/ckanext/nhs/fanstatic/css"))
  .pipe(cleanCss())
  .pipe(rename({ suffix: '.min' }))
  .pipe(dest(__dirname + "/ckanext/nhs/fanstatic/css"));


const watchSource = () =>
  watch(
    __dirname + "/ckanext/nhs/fanstatic/sass/**/*.scss",
    { ignoreInitial: false },
    build
  );

exports.build = build;
exports.watch = watchSource;
