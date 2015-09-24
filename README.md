# Covalic, a web application for hosting grand challenges

These instructions should clearly be expanded, but for now, here is the simplest
way to tell if your end-to-end Covalic setup is working.

Assumes you have a Covalic system running.

  1. login to the Covalic web app with an admin user
  2. create a new challenge from the challenges page, named 'test challenge'
  3. create a new phase in your challenge, named 'test phase', checking the checkbox to make it active
  4. in the Girder web app, in the 'test challenge' collection, 'test phase' folder, 'Ground truth' folder, upload a single ground truth file
  5. in the Covalic web app, go to the page for 'test phase', click the 'Participate in this phase' button
  6. click the 'Submit your results' button, create a submission uploading the same ground truth file, click the 'Start upload' button
 
If your system is fully operational, you will see a score returned.  
