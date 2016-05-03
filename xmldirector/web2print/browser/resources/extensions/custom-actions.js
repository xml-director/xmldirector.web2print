KEY = 'NIMBUDOCS_HTML';
Storage = window.localStorage;
if (typeof(Storage) == "undefined") {
    alert('Local storage is not supported by your browser. Please disable "Private Mode", or upgrade to a modern browser.');
}

function initCustomActions(editor){

    editor.addEventListener("local-save", "actioninvoke", function(e) {
        editor.fetchDocument().then(function(v) {
            Storage.setItem(KEY, v);
        });
    });

    editor.addEventListener("local-restore", "actioninvoke", function(e) {
        editor.fetchDocument().then(function(v) {
            var html = Storage.getItem(KEY);
            if (html != "undefined") {
                if (confirm('Do you really want to restore content from last locally saved state?')) {
                    editor.loadDocument(html, CONTENT_URL);
                    alert('restored');
                }
            }
        });
    });

    editor.addEventListener("exit", "actioninvoke", function(e) {
        if (confirm('Do you really want to leave the editor without saving?')) {
            Storage.removeItem(KEY);
            window.location.href = WEB2PRINT_URL;
        }
    });
    
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
                    Storage.removeItem(KEY);
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
