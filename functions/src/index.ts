import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin'

// // Start writing Firebase Functions
// // https://firebase.google.com/docs/functions/typescript
//
//
admin.initializeApp();

export const makeUserEntry = functions.auth.user().onCreate((user) => {
    const user_entry = {
        type: {
            role: "student",
            group: 0 // change this later
        },
        tasks: {
            complete: [],
            assigned: [],
            total: 0,
            remaining: 0
        },
        limits: {
            min: 3,
            max: 10000,
            types: []
        }
    };
    const result = admin.firestore().collection('users').doc(user.uid).set(user_entry);
    return result;
});

//export const getTaskForUID = functions.https.onCall((data, context) => {
//    // Do stuff
//    const uid = context.auth.uid;
//    function random_incomplete_element() {
//        const rnd = Math.random()
//        admin.firestore().collection('tasks').select()
//    }
// });
