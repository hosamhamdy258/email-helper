document.addEventListener("DOMContentLoaded", function () {
  const templateSelect = document.getElementById("id_template");
  const subjectField = document.getElementById("id_subject");

  if (templateSelect && subjectField) {
    templateSelect.addEventListener("change", function () {
      const templateId = this.value;

      if (templateId) {
        // Show loading indicator
        const originalSubject = subjectField.value;

        // Fetch template data
        fetch(`/admin/emails/sentemail/get-template/${templateId}/`)
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              subjectField.value = data.subject;

              const editorElement = document.querySelector(".fr-element");
              if (editorElement) {
                editorElement.innerHTML = data.body;
                editorElement.focus();
                subjectField.focus();
              }
            }
          })
          .catch((error) => {
            console.error("Error fetching template:", error);
            subjectField.value = originalSubject;
          });
      }
    });
  }
});
