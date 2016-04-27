function initCustomActions(editor){
    var newDocumentOverride = editor.getAction("new-document");
    if (newDocumentOverride !== null) {
        newDocumentOverride.addInvokeListener(function(e) {
            var response = jQuery.get("source/template.html", function(data){
                editor.loadDocument(data);
            });
            
            e.preventDefault();
        });
    }
    
    editor.addEventListener("save-and-close", "actioninvoke", function(e) {

        editor.fetchDocument().then(function(v) {
            var html = v
            var pdf_url = editor.getPdfUrl();
            var context_url = $('base').attr('href');
            var data = {html: html,
                        pdf_url: pdf_url,
                        template: TEMPLATE
                       };

            $('#message').text('Saving....');
            $.ajax({
                type: 'POST',
                url: CONTEXT_URL + '/@@xmldirector-web2print-nimbudocs-set-content', 
                data: data, 
                success: function(return_url) {
                    $('#message').text('Saved...returning to Web-to-Print application');
                    window.location.href = return_url;
                },
                error: function() {
                    $('#message').text('Error while saving....');
                }
            });
        });
    });
}
