$(document).ready(function() {
    var $inputs = $(".code-input"); // تغییر selector

    $inputs.attr("maxlength", 1);

    $inputs.on("input", function() {
        var $this = $(this);
        // فقط عدد
        $this.val($this.val().replace(/[^0-9]/g, ""));
        if ($this.val()) {
            var allInputs = $this.closest(".code-fields").find(".code-input");
            var idx = allInputs.index($this);
            if (idx < allInputs.length - 1) {
                allInputs.eq(idx + 1).focus();
            }
        }
    });

    $inputs.on("keydown", function(e) {
        if (e.key === "Backspace") {
            var $this = $(this);
            if (!$this.val()) {
                var allInputs = $this.closest(".code-fields").find(".code-input");
                var idx = allInputs.index($this);
                if (idx > 0) allInputs.eq(idx - 1).focus();
            }
        }
    });

    $inputs.on("paste", function(e) {
        e.preventDefault();
        var pasteData = (e.originalEvent || e).clipboardData.getData("text").replace(/[^0-9]/g, "");
        var allInputs = $(this).closest(".code-fields").find(".code-input");
        allInputs.each(function(i, input) {
            input.value = pasteData[i] || '';
        });
        var lastFilled = allInputs.eq(Math.min(pasteData.length, allInputs.length) - 1);
        if (lastFilled.length) lastFilled.focus();
    });
});
