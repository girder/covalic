<%include file="_header.mako"/>

<p>
An error occurred while scoring the submission named
<b>${submission['title']}</b>
to the challenge
<b>${challenge['name']} (${phase['name']})</b>
from user <b>${user['login']}</b>
(<b><a href="mailto:${user['email']}">${user['firstName']} ${user['lastName']}</a></b>):
</p>

% if log:
<p>
Log output:
</p>
<pre>
${log}
</pre>
% else:
<p>
No log is available.
</p>
% endif

<p>
You can also view these results
<a href="${host}#submission/${submission['_id']}">here</a>.
</p>

<p>
You were sent this alert because you are an administrator of this
phase and/or challenge.
</p>

<%include file="_footer.mako"/>
