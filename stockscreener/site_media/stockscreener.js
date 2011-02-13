

function addCriteria(tableId, selected) {
	// select table, go down to the TR level, and insert the new row After.
	new Ajax.Request('/search/criteria/'+selected.value+'/', {
		method: 'GET',
		onSuccess: function(transport) {
			$(tableId).down('tr').insert({after: transport.responseText});
		},
		onException: function(transport, e) {
			alert('Error! ' + e);
		}
	});
}

function removeCriteria(href) {
	href.up('tr').remove();
}

function search(resultId, aForm) {
    // create request as ajax
    new Ajax.Updater(resultId, aForm.action, {
        parameters: aForm.serialize()
    });
    return false;
}
