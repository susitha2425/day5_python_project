function updateClock() {
    const clock = document.getElementById("live-time");
    if (clock) {
        clock.textContent = new Date().toLocaleTimeString();
    }
}

updateClock();
window.setInterval(updateClock, 1000);

$(function () {
    function validateAge(showEmptyMessage) {
        const ageField = $("#age");
        const age = ageField.val().trim();
        let message = "";

        if (!age && showEmptyMessage) {
            message = "Please enter your age.";
        } else if (age && !/^\d+$/.test(age)) {
            message = "Enter age using numbers only.";
        } else if (age && Number(age) < 1) {
            message = "Age must be a positive number.";
        }

        ageField.toggleClass("is-invalid", Boolean(message));
        $("#age-feedback").text(message);
        return !message;
    }

    $("#age").on("input", function () {
        validateAge(false);
    });

    $("#registration-form").on("submit", function (event) {
        const name = $("#name").val().trim();
        const email = $("#email").val().trim();
        const age = $("#age").val().trim();
        const gender = $("#gender").val();
        const course = $("#course").val();
        const password = $("#password").val();

        if (!validateAge(Boolean(age))) {
            event.preventDefault();
            $("#age").trigger("focus");
            return;
        }
        if (!name || !email || !age || !gender || !course || !password) {
            window.alert("Please complete all required fields.");
            event.preventDefault();
            return;
        }
        if (password.length < 6) {
            window.alert("Password must be at least 6 characters long.");
            event.preventDefault();
        }
    });

    $("#toggle-details").on("click", function () {
        const details = $("#profile-details");
        details.toggle();
        $(this).text(details.is(":visible") ? "Hide Details" : "Show Details");
    });

    $("#course-select").on("change", function () {
        const course = $(this).val();
        $.post("/update-course", { course: course })
            .done(function (response) {
                $("#profile-course").text(response.course);
                window.alert("Course updated to: " + response.course);
            })
            .fail(function (xhr) {
                const message = xhr.responseJSON && xhr.responseJSON.error
                    ? xhr.responseJSON.error
                    : "Course could not be updated. Please try again.";
                window.alert(message);
            });
    });
});
