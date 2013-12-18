<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="">
    <meta name="author" content="">
    <link rel="shortcut icon" href="static/favicon.png">

    <title>OpenNX Kickstart</title>

    <link href="static/css/bootstrap.min.css" rel="stylesheet">
    <link href="static/css/basic.css" rel="stylesheet">

    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/libs/html5shiv/3.7.0/html5shiv.js"></script>
      <script src="https://oss.maxcdn.com/libs/respond.js/1.3.0/respond.min.js"></script>
    <![endif]-->
  </head>

  <body>

    <div class="navbar navbar-inverse navbar-fixed-top" role="navigation">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="#">Kickstart</a>
        </div>
        <div class="collapse navbar-collapse">
          <ul class="nav navbar-nav">
          %for p,t in menu_items:
          % cls = ['', 'active'][bool(current_page==p)]
            <li class="{{cls}}"><a href="{{p}}">{{t}}</a></li>
          %end
          </ul>
        </div><!--/.nav-collapse -->
      </div>
    </div>

    <div class="container">
      <div class="starter-template">
        <h1>OpenNX Kickstart Installer</h1>
        <p class="lead">Use this <i>page</i> to install all prerequisities and NX components on this machine.</p>
        % print """<p class="lead">Use <b>this</b> page to install all prerequisities and NX components on this machine.</p>"""
      </div>
    </div><!-- /.container -->

    <script src="https://code.jquery.com/jquery-1.10.2.min.js"></script>
    <script src="static/js/bootstrap.min.js"></script>
  </body>
</html>
