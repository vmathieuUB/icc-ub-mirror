/**
 * @file
 * Gdheader utilities.
 *
 */

(function ($, Drupal, drupalSettings) {
  'use strict'

  Drupal.behaviors.gdheader = {
    attach: function (context, settings) {
      //console.log('Behaviour gd header')
      // estils via jQuery
      //console.log(settings);
      
      $('.parallax').parallax();

    }
  } 
  

})(jQuery, Drupal, drupalSettings)
