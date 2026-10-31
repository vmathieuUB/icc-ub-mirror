/**
 * @file
 * Yearpicker call.
 *
 */

(function ($, Drupal, drupalSettings) {
  'use strict'

  Drupal.behaviors.icc_yearpicker = {
    attach: function (context, settings) {
        //console.log('Behaviour Year Picker');
        //console.log(context);
        //console.log("total_rows:" + drupalSettings.total_rows + " // year: " + drupalSettings.yearvalue);
  
        var currentYear = "";
        if (drupalSettings.yearvalue != "") {
          currentYear = drupalSettings.yearvalue;
        }else{
          currentYear =  (new Date).getFullYear();
        }
          
        //var data_selector = "field-year-value";
        //var $input = $("input[data-drupal-selector=edit-" + data_selector + "]");
  
        $("input[name='field_year_value']").yearpicker({
          year: parseFloat(currentYear),
          startYear: parseFloat(2006),
          endYear: parseFloat(currentYear)
        });
          
    }
  } 
  
})(jQuery, Drupal, drupalSettings)
