$(document).ready(function () {
    // Add a new feature form
    $('#add_feature').click(function () {
        var totalForms = parseInt($('#id_feature-TOTAL_FORMS').val());
        var newForm = $('.feature-form:first').clone();

        if (newForm.length === 0) {
            console.error('No feature form found to clone. Check your HTML structure.');
            return;
        }

        newForm.find(':input').each(function () {
            var name = $(this).attr('name').replace(/\d+/, totalForms);
            var id = $(this).attr('id').replace(/\d+/, totalForms);

            $(this).attr({ name: name, id: id }).val('');
            parseInt($('#id_feature-TOTAL_FORMS').val(totalForms+1))
        });

        $('#feature_box').append(newForm);
        $('#id_form-TOTAL_FORMS').val(totalForms + 1);
    });

    // Add a new image form
    $('#add_img').click(function () {
        var imgTotalForms = parseInt($('#id_img-TOTAL_FORMS').val());
        var newForm = $('#pure_img:first').clone();
        if (newForm.length === 0) {
            console.error('No image form found to clone. Check your HTML structure.');
            return;
        }

        newForm.find(':input').each(function () {
            var name = $(this).attr('name').replace(/\d+/, imgTotalForms);
            var id = $(this).attr('id').replace(/\d+/, imgTotalForms);

            $(this).attr({ name: name, id: id }).val('');
            parseInt($('#id_img-TOTAL_FORMS').val(imgTotalForms+1));
        });
        newForm.show();
        newForm.removeAttr("id").addClass("img-form");
        newForm.find('input').prop("disabled", false);

        newForm.find('a').remove();
        newForm.contents().filter(function () {
            return this.nodeType === 3;
        }).remove();

        newForm.contents().filter(function() {
            return this.nodeType === 3 && $.trim(this.nodeValue) !== "";
        }).remove();

        newForm.find("*").contents().filter(function() {
            return this.nodeType === 3 && $.trim(this.nodeValue) !== "";
        }).remove();

        newForm.find('input[type="file"]').each(function() {
            var input = $(this);
            if (!$('label[for="' + input.attr('id') + '"]').length) {
                var label = $('<label>').attr('for', input.attr('id')).text('تصویر:');
                input.before(label);
            }
        });

        $('#img_box').append(newForm);
        $('#id_form-TOTAL_FORMS').val(imgTotalForms + 1);
    });

    // Delete feature form
    $(document).on('click', '#delete-feature', function () {
        let num = parseInt($('#id_feature-TOTAL_FORMS').val());
        if (num > 1){
        $('.feature-form').last().remove();
        parseInt($('#id_feature-TOTAL_FORMS').val(num - 1));
        }
    });

    // Delete image form
    $(document).on('click', '#delete-img', function () {
        let num = parseInt($('#id_img-TOTAL_FORMS').val());
        if (num > 1){
        $('.img-form').last().remove()
        parseInt($('#id_img-TOTAL_FORMS').val(num - 1));
        }

    });
});

$(document).ready(function () {
    var FirstTotalColors = parseInt($('#id_color-TOTAL_FORMS').val());
    var FirstTotalSizes = parseInt($('#id_size-TOTAL_FORMS').val());
    $("#size-checkbox").change(function () {
        if ($(this).is(":checked")) {
            $("#size-container").show();
        } else {
            $("#size-container").hide().find('input, select, textarea').prop('disabled', true);;
        }
    });
    $('#add_size').click(function () {
        var totalForms = parseInt($('#id_size-TOTAL_FORMS').val());
        var newForm = $('#size:first').clone();

        if (newForm.length === 0) {
            console.error('No feature form found to clone. Check your HTML structure.');
            return;
        }

        newForm.find(':input').each(function () {
            var name = $(this).attr('name').replace(/\d+/, totalForms);
            var id = $(this).attr('id').replace(/\d+/, totalForms);

            $(this).attr({ name: name, id: id }).val('');
            parseInt($('#id_size-TOTAL_FORMS').val(totalForms+1))
        });

        let addBtn = $('#add_size').detach();
        let removBtn = $('#delete-size').detach();
        $('#size-container').append(newForm);
        $('#size-container').append(removBtn)
        $('#size-container').append(addBtn);
        $('#id_form-TOTAL_FORMS').val(totalForms + 1);
    });

    $(document).on('click', '#delete-size', function () {
        let num = parseInt($('#id_size-TOTAL_FORMS').val());
        if (num > FirstTotalSizes){
        $('#size-container #size').last().remove();
        parseInt($('#id_size-TOTAL_FORMS').val(num - 1));
        }
    });

    $(document).ready(function () {
    $("#color-checkbox").change(function () {
        if ($(this).is(":checked")) {
            $("#color-container").show();
        } else {
            $('#color-container #color').find('input, select, textarea').prop('disabled', true);
            $("#color-container").hide();
            parseInt($('#id_color-TOTAL_FORMS').val(0));
        }
    });
});
$('#add-color').click(function () {
    var totalForms = parseInt($('#id_color-TOTAL_FORMS').val());
    var newForm = $('#color:first').clone();

    if (newForm.length === 0) {
        console.error('No feature form found to clone. Check your HTML structure.');
        return;
    }

    newForm.find(':input').each(function () {
        var name = $(this).attr('name').replace(/\d+/, totalForms);
        var id = $(this).attr('id').replace(/\d+/, totalForms);

        $(this).attr({ name: name, id: id }).val('');
        parseInt($('#id_color-TOTAL_FORMS').val(totalForms+1))
    });

    let addBtn = $('#add-color').detach();
    let removeBtn = $('#delete-color').detach();
    $('#color-container').append(newForm);
    $('#color-container').append(removeBtn);
    $('#color-container').append(addBtn);
    $('#id_form-TOTAL_FORMS').val(totalForms + 1);
});
$(document).on('click', '#delete-color', function () {
    let num = parseInt($('#id_color-TOTAL_FORMS').val());
    if (num > FirstTotalColors){
    $('#color-container #color').last().remove();
    parseInt($('#id_color-TOTAL_FORMS').val(num - 1));
    }
});
});
    $(".more_img_checkbox").change(function () {
        let counter = $(this).data('counter')
        if ($(this).is(":checked")) {
            $("#more_img_"+counter).show();
        } else {
            $("#more_img_"+counter).hide();
        }
    });
