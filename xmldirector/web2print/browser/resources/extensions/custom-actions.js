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
    
    // the brush tool
    editor.addEventListener("draw-shape-brush", "actioninvoke", function(e) {
        this.selectedState = true;
        
        var action = this;
        
        var properties = {
            lineWidth: "15"
        };
        
        editor.invokeAction("draw-shape-freehand", properties).then(function() {
            action.selectedState = false;
        });
    });
}