/**
 * @file
 * Global utilities.
 *
 */

(function ($, Drupal) {
  'use strict'

  Drupal.behaviors.bootstrap_barrio_subtheme = {
    attach: function (context, settings) {
      $('.page-node-1 .carousel').wrap(
        '<div class="col-12 col-md-10 col-lg-8" />'
      )
      
      $('.triple .view-content').addClass('ml-sm-1 mr-sm-1')

      /*
       *   Ajustar límit superior pàgina a la barra d'eines d'administració si hi és
       */
      $(window).on('load', function () {
        $('.fixed-top').css('top', $('body').css('padding-top'))
        console.log('window load: ' + $('body').css('padding-top'))
      })

      $('.toolbar-toggle-orientation, .toolbar-tab').on('click', function () {
        setTimeout(function () {
          var padding = '39px'
          if (
            $('body.toolbar-fixed.toolbar-tray-open.toolbar-horizontal').length
          ) {
            padding = '79px'
            // console.log(padding);
          }
          $('.fixed-top').css('top', padding)
          // console.log("All" + padding);
        }, 500)
      })
      
    }
  }

})(jQuery, Drupal)
