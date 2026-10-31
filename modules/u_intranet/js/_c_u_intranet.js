var _c_u_intranet = {};

_c_u_intranet.opr_login = function() {

    $("#message_login").html("");
    $("#error_username").hide();
    $("#error_password").hide();

    var oValid = true;

    if (trim($("#username").val()) == "") {

        oValid = false;
        $("#error_username").show();

    }

    if (trim($("#password").val()) == "") {

        oValid = false;
        $("#error_password").show();

    }

    if (oValid) {

        $.ajax({
            type: "POST",
            url: 'index.php?m=u_intranet&c=u_intranet&op=opr_login',
            data: "username=" + encodeURIComponent($("#username").val()) + "&password=" + encodeURIComponent($("#password").val()),
            dataType: "text",
            success: function(oDataResponse) {

                if (parseInt(oDataResponse) == 1)
                    location.href = "index.php?m=u_intranet&c=u_intranet&op=frm_intranet";
                else {
                    $("#btn_login").show();
                    $("#btn_clean_fields").show();
                    $("#message_login").html("The login data you entered are not valid. Try once more !");
                }

            }
        });

        $("#btn_login").hide();
        $("#btn_clean_fields").hide();

    }

}

_c_u_intranet.opr_clean_fields = function() {

    $("#message_login").html("");
    $("#error_username").hide();
    $("#error_password").hide();
    $("#username").val("");
    $("#password").val("");

}

_c_u_intranet.opr_change_password = function() {

    $("#error_cp_pass_old").hide();
    $("#error_cp_pass_new").hide();
    $("#error_cp_pass_again").hide();
    $("#error_diff_pass").hide();

    var oOld = trim($("#cp_pass_old").val());
    var oNew = trim($("#cp_pass_new").val());
    var oNewAgain = trim($("#cp_pass_again").val());

    var oValid = true;

    if (oOld == "") {

        oValid = false;
        $("#error_cp_pass_old").show();

    }

    if (oNew == "") {

        oValid = false;
        $("#error_cp_pass_new").show();

    }

    if (oNewAgain == "") {

        oValid = false;
        $("#error_cp_pass_again").show();

    }

    if (oNew != oNewAgain) {

        oValid = false;
        $("#error_diff_pass").show();

    }

    if (oValid) {

        help_functions.default_callback_data = ["message_user_password",
            "btn_change_password",
            function(oData) {
                var oParts = oData.split("<|>");
                if (parseInt(oParts[0]) == 1) {
                    $("#cp_pass_old").val("");
                    $("#cp_pass_new").val("");
                    $("#cp_pass_again").val("");
                }

            }
        ];

        $.ajax({
            type: "POST",
            url: 'index.php?m=u_intranet&c=u_intranet&op=opr_change_password',
            data: 'old_pass=' + encodeURIComponent(oOld) + '&new_pass=' + encodeURIComponent(oNew),
            dataType: "text",
            success: help_functions.default_callback
        });

        $("#btn_change_password").hide();

    }

}

_c_u_intranet.opr_send_new_password = function() {

    $("#error_empty_email").hide();
    $("#error_valid_email").hide();
    $("#error_email_not_sent").hide();
    var bValid = true;

    if (trim($("#new_password").val()) == "") {

        $("#error_empty_email").show();
        bValid = false;

    }

    if (bValid) {

        $.ajax({
            type: "POST",
            url: 'index.php?m=u_intranet&c=u_intranet&op=opr_send_new_password',
            data: 'email=' + $("#new_password").val(),
            dataType: "text",
            success: function(oData) {

                var oParts = oData.split("|");

                if (parseInt(oParts[0]) == 1) {

                    $("#new_password").val("");
                    alert("Your new password has been successfuly sent to the following address: " + oParts[1]);

                } else if (parseInt(oParts[0]) == -1) {

                    $("#error_valid_email").show();

                } else if (parseInt(oParts[0]) == -2) {

                    $("#error_email_not_sent").show();

                }

                $("#btn_forgotten_mail").show();

            }
        });

        $("#btn_forgotten_mail").hide();

    }


}


_c_u_intranet.opr_optimize_js = function() {

    $("#message_optimize_js").html("");

    var oNotify = noty({text: 'Do not refresh the page until you get a message !', modal: true, layout: 'center'});
    $.ajax({
        type: "POST",
        url: 'index.php?m=u_intranet&c=u_intranet&op=opr_optimize_site_scripts',
        dataType: "text",
        success: function(sResponse) {

            var oParts = help_functions.get_response_parts(sResponse);
            $("#message_optimize_js").html(oParts[1]);
            $("#btn_optimize_js").show();
            oNotify.close();

        }
    });

    $("#btn_optimize_js").hide();

}



