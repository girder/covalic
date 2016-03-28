<%include file="_header.mako"/>

<p>
An error occurred while scoring your submission named
<b>${submission['title']}</b>
to the challenge
<b>${challenge['name']} (${phase['name']})</b>:
</p>

% if log:
<pre>
${log}
</pre>
% else:
<p>
No log is available.
</p>
% endif

<p>
Please fix the error and try again.
</p>

<%include file="_footer.mako"/>
