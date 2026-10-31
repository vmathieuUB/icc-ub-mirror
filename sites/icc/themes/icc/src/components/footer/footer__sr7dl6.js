/**
 * @file
 * Footer utilities.
 *
 */
(function ($, Drupal) {

  'use strict';

  console.log("footer.js ");

  /*
  Drupal.behaviors.social_sharing = {
    attach: function (context, settings) {
      console.log("Behaviour social_sharing @footer.js ");

      var Share = {
        facebook: function(purl, ptitle, pimg, text) {
          url = 'http://www.facebook.com/sharer.php?s=100';
          url += '&p[title]=' + encodeURIComponent(ptitle);
          url += '&p[summary]=' + encodeURIComponent(text);
          url += '&p[url]=' + encodeURIComponent(purl);
          url += '&p[images][0]=' + encodeURIComponent(pimg);
          Share.popup(url);
        },
        twitter: function(purl, ptitle) {
          var url="";
          url = 'http://twitter.com/share?';
          url += 'text=' + encodeURIComponent(ptitle);
          url += '&url=' + encodeURIComponent(purl);
          url += '&counturl=' + encodeURIComponent(purl);
          Share.popup(url);
        },
        popup: function(url) {
          //window.open(url,'','toolbar=0,status=0,width=626, height=436');
          window.open(url,'_blank');
        }
      };

      $('#share-twitter').on("click", function(){
        console.log("URI: " + settings.current_uri);
        console.log("TITLE: " + settings.page_title);
        Share.twitter(settings.current_uri, settings.page_title);
      });
      $('#follow-twitter').on("click", function(){
        window.open(settings.followus_twitter,'_blank');
      });
    }
  }   
  */

  // When user scrolls down 80px from the top of the document, show the button
  $(window).on("scroll", function(){
    scrollFunction();
  });

  $("#btnBackTop").click(function(){
    $("html, body").animate({scrollTop: 0}, 500);
  });

  function scrollFunction() {
    if (document.body.scrollTop > 80 || document.documentElement.scrollTop > 80) {
      document.getElementById("btnBackTop").style.display = "block";
    } else {
      document.getElementById("btnBackTop").style.display = "none";
    }
  }

})(jQuery, Drupal);


