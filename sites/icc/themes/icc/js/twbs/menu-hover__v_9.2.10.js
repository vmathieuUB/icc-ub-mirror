/**
 * @file
 * Bootstrap Menu overrides: adds dropdown on hover effect.
 * Code from: https://webdesign.tutsplus.com/tutorials/how-to-make-the-bootstrap-navbar-dropdown-work-on-hover--cms-33840
 * Thanks to: https://tutsplus.com/authors/george-martsoukos?_ga=2.161175293.1597861582.1599730694-1853861820.1599730694
 */

(function ($, Drupal) {
    'use strict'
    
    const $dropdown = $(".dropdown");
    const $dropdownToggle = $(".dropdown-toggle");
    const $dropdownMenu = $(".dropdown-menu");
    const showClass = "show";
     
    $(window).on("load resize", function() {

      if (this.matchMedia("(min-width: 768px)").matches) {
        $dropdown.hover(
          function() {
            const $this = $(this);
            $this.addClass(showClass);
            $this.find($dropdownToggle).attr("aria-expanded", "true");
            $this.find($dropdownMenu).addClass(showClass);
          },
          function() {
            const $this = $(this);
            $this.removeClass(showClass);
            $this.find($dropdownToggle).attr("aria-expanded", "false");
            $this.find($dropdownMenu).removeClass(showClass);
          }
        );
      } else {
        $dropdown.off("mouseenter mouseleave");
      }

    }); 
    
})(jQuery, Drupal)