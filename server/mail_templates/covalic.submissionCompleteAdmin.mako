<%include file="_header.mako"/>

<div style="font-size: 18px; font-weight: bold; color: #009933; margin-bottom: 12px;">
A submission has been scored successfully.
</div>

<p>
A submission to the challenge <b>${challenge['name']} (${phase['name']})</b>
from user <b>${user['login']}</b>
(<b><a href="mailto:${user['email']}">${user['firstName']} ${user['lastName']}</a></b>)
named <b>${submission['title']}</b> has finished processing.
You can view the results
<a href="${host}#submission/${submission['_id']}">here</a>.
</p>

<%include file="_footer.mako"/>
