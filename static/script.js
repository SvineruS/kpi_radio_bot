// Code goes here

$(function() {
  var $previewContainer = $('#comment-md-preview-container');
  $previewContainer.hide();
  var $md = $("#comment-md").markdown({
    autofocus: false,
    height: 270,
    iconlibrary: 'fa'
  });
})