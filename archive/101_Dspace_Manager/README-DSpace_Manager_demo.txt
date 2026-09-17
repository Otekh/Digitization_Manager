OTEKH DSpace Manager — Test Version

Hi,

Attached is the current test version of the OTEKH DSpace Manager.

The purpose of this app is to test a replacement for our current Excel-based digitization/metadata workflow. Rather than students entering metadata into Excel and then having that information manually re-entered into DSpace, the student creates the archival record directly in this app, attaches the associated digitized files, and submits the record for manager review.

For now, nothing is being sent to DSpace. This version is specifically for testing the intake, file-management, and review workflow.

Installing / Opening
Download OTEKH DSpace Manager.zip.
Double-click the ZIP to extract it.
You should now have OTEKH DSpace Manager.app.
Move the app to your Applications folder if you like, or simply run it from where you extracted it.
Double-click OTEKH DSpace Manager to open it.
If macOS blocks the app

This is a test application and has not yet been signed/notarized for public distribution, so macOS may initially say that it cannot verify the developer.

First try:

Right-click / Control-click OTEKH DSpace Manager.app → Open → Open

If macOS still blocks it:

System Settings → Privacy & Security

Scroll down. You may see a message saying that OTEKH DSpace Manager was blocked. Choose Open Anyway, authenticate if requested, and then open the application again.

You should only have to do this the first time.

Note: This particular test build is for an Apple Silicon Mac (M1/M2/M3/M4/M5).

Using the App

The basic workflow is:

Create Record → Add Metadata → Attach Files → Save Draft → Submit for Review → Manager Reviews → Approve or Return

1. Create a record

Choose New Record.

Enter the available archival metadata. The record does not need to be complete before you save it.

Save Draft means exactly that: you can save an incomplete record and return to it later.

2. Attach the digitized files

Files can be attached while creating the record. You do not need to finish the metadata first.

Choose Attach Files and select the relevant scan, PDF, image, audio, video, or other archival file.

The important thing to test here is that the app is not merely remembering where the original file was located. It copies the file into the record's own managed folder.

The original source file is left alone.

3. Where the actual records and files live

The app creates a visible working archive on the Mac at:

Documents → OTEKH DSpace Manager → Records

Each archival record gets its own folder.

For example:

Documents
└── OTEKH DSpace Manager
    └── Records
        └── 20220000_OTEK_example-record_BKscn
            ├── record.json
            └── [associated archival files]

Please feel free to actually look inside this folder while testing. That's intentional.

The idea is that each record becomes a self-contained package consisting of its metadata + associated files, ready for the eventual DSpace transfer process.

4. Record naming

The folder name is generated from the archival metadata.

Importantly, the date at the beginning is the date associated with the archival object/record, not today's scanning date.

So an item from 2022 may correctly produce something beginning with:

20220000_...

This naming scheme can still be adjusted based on what we ultimately need for DSpace.

5. Submit for Review

Once the student believes the record is complete, choose Submit for Review.

Unlike Save Draft, submission checks that the required information has actually been provided.

The record then moves into the manager-review workflow.

6. Manager Review

Open the Review area.

The manager can inspect:

the submitted metadata
associated files
record information
submission status

The manager can then either Approve the record or Return it for corrections.

The goal is to retain the quality-control step we currently have while eliminating the need for the manager to retype the student's metadata into another system.

7. Transfer

Once a manager approves a record, it should appear in:

Transfer → Ready for Transfer

You'll also see an OTEKH Lab Repository connection area with controls such as:

Connect to Lab
Sync Approved Records

These are intentionally NOT FUNCTIONAL YET.

They are there to demonstrate the intended next stage of the workflow.

Eventually, this is where our technical/DSpace people can connect the app to the actual lab repository and determine the appropriate DSpace ingest/API/package process.

What IS Working in This Version

The important things to test right now are:

Creating archival records
Editing metadata
Saving incomplete drafts
Attaching files
Copying those files into managed record folders
Generated archival record/folder names
Viewing existing records
Submitting records for manager review
Manager review
Returning records for correction
Approving records
Approved records appearing as Ready for Transfer
Persistent local record/file storage
What is NOT wired yet

This version does not currently:

connect to the OTEKH Lab server
connect directly to DSpace
upload records to DSpace
synchronize between student computers and the lab
perform final DSpace ingest/package mapping
replace or modify anything in the existing DSpace repository

So there is no danger during this test of accidentally uploading test records into the real archive.

The Transfer screen is currently a demonstration of where that functionality will eventually live.

What I Want Us to Test

For this round, I'm primarily interested in whether this actually makes sense as a replacement for the Excel workflow.

Please don't worry about whether every button, label, metadata field, or visual detail is perfect yet.

I'd especially like feedback on whether:

the metadata fields correspond to what we actually need;
anything important from the current Excel sheet is missing;
any fields are unnecessary;
creating a record feels faster/easier than using Excel;
attaching and managing files makes sense;
the student → manager review process makes sense;
the manager needs additional controls or information during review;
the generated folder/file organization makes sense for our actual archive;
anything in the workflow is confusing or requires unnecessary extra steps; and
there is anything we need to preserve specifically for eventual DSpace ingest.

The main question for this test is very simple:

Can this become a clean intake and quality-control system that lets students do the initial archival record creation, while giving the manager an easy review/approval process before anything enters DSpace?

The DSpace connection itself comes later.