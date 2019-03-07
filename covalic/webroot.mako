<!DOCTYPE html>
<html lang="en">
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Covalic</title>
    <link rel="stylesheet" href="/static/built/girder_lib.min.css">
    <link rel="icon" type="image/png" href="/static/built/Girder_Favicon.png">
    % for plugin in pluginCss:
    <link rel="stylesheet" href="/static/built/plugins/${plugin}/plugin.min.css">
    % endfor
  </head>
  <body>
    <div id="g-global-info-apiroot" class="hide">/api/v1</div>
    <script src="/static/built/girder_lib.min.js"></script>
    <script src="/static/built/girder_app.min.js"></script>
    % for plugin in pluginJs:
    <script src="/static/built/plugins/${plugin}/plugin.min.js"></script>
    % endfor
    <script src="/static/built/plugins/covalic_external/plugin.min.js"></script>
  </body>
</html>
