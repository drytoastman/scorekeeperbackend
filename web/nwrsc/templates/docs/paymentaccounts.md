
# Payment Accounts

We current integrate with two type of accounts, **Square** and **PayPal**.  All configured accounts for a series can be viewed
from the accounts page on the admin site.  Settings &rarr; Payment Accounts.  Once setup, you can assign payment accounts to each
event from the event edit page.

## Item Lists

All online payments are expected to have a list of items that the user can select from.  i.e. Member Entry and Non-Member Entry.
Square lists are automatically created from the account location.  Paypal lists are manually created by the user.

## Square Accounts

Scorekeeper is setup as a Square application that you can authorize to lookup items and perform transactions on your account.
The Scorekeeper app will use the item list from one of your locations as the items available to the end user.

1. Before Authorizing

    Before you authorize the Scorekeeper application, it is suggested that you have created a location in your square account and 
    only assigned items to that location that you wish to allow for online payment.

2. Authorize Scorekeeper
 
    From the payment accounts page, click **Setup/Update A Square Location**.  This should bring up a square page where you can
    login to your account and authorize Scorekeeper which produces a 30-day token for Scorekeeper to use.

    After this is successful, you will be presented with a list of your Square locations.  Select the location you wish to use for
    Scorekeeper payments.  You should be returned to the payment accounts page which know includes an entry for your Square account.

3. Periodic Updates

    Scorekeeper should automatically attempt to update the access token every 30 days without user intervention.

## PayPal Accounts

Paypal setup is a little more manual.  We do **NOT** use your account email or password.  Instead we rely on their REST API and an
app that you setup from your paypal account.  

1. App Setup

    To setup your app, see the paypal documentation at <https://developer.paypal.com/docs/integration/admin/manage-apps/>.  You may need
    to setup developer access to do so.  The created app just needs to allow Accept Payments, nothing else.

2. Add App To Scorekeeper

    From the payment accounts page, click **Add PayPal App**. The values to enter are:
    * Account Name - A user provided name 
    * Client Id - The **Client ID** field from the **LIVE** version of your PayPal App
    * Client Secret - The enabled **Secret** from your PayPal App

3. Create Items

    You can now create the list of items that are avaiable for online payments.  Click Add Item and enter:
    * Item Name - The visible name for the item such as Member Entry
    * Price - The amount for a single item such as 30.00

