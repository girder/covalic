<%include file="_header.mako"/>

<div style="font-size: 18px; font-weight: bold; color: #009933; margin-bottom: 12px;">
Your submission has been scored successfully.
</div>

<p>
Your submission named <b>${submission['title']}</b> to the challenge
<b>${challenge['name']} (${phase['name']})</b> has finished processing. You can
view the results <a href="${host}#submission/${submission['_id']}">here</a>.
</p>

<p>
Please note that this submission overrode any previous submissions that you
made to this phase of the challenge; only your latest score will appear in the
leader board.
</p>

<%include file="_footer.mako"/>
