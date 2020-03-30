import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin'

// // Start writing Firebase Functions
// // https://firebase.google.com/docs/functions/typescript
//
//
admin.initializeApp();

async function usersForGroup(role : string, set_ : number) : Promise<Array<string>>{
    return admin.firestore().collection("users")
        .where(`type.role`, "==", role)
        .where(`type.set`, "==", set_)
        .get()
        .then(qset => {
            return qset.docs.map(v => v.id)
        }).catch(_ => {return []})
}

async function tasksForGroup(role : string, set_ : number) : Promise<Array<string>>{
    console.log(`Finding all tasks for ${role}-${set_}`)
    return admin.firestore().collection("taskset")
        .where(`groups.${role}`, "array-contains", set_)
        .get()
        .then(qset => {
            console.log("tasksforgroup - success")
            console.log(qset)
            console.log(qset.docs.length)
            return tasksForTasksets(qset.docs.map(v => v.id))
        }).catch(_ => {
            console.log("tasksforgroup - failure")
            console.log(_)
            return []
        })
}

async function tasksForTasksets(tasksets : Array<string>) : Promise<Array<string>>{
    return admin.firestore().collection("tasks")
        .where("taskset", "in", tasksets)
        .get()
        .then(tasks => tasks.docs.map(t => t.id))
        .catch(_ => [])
}

function updateTasksForUser(userid : string) : any {
    console.log(`UpdateTasksForUser: ${userid}`)
    const user_ref = admin.firestore()
        .collection('users')
        .doc(userid)
    return user_ref.get().then(user => {
            const role = user.get("type.role")
            const set_ = user.get("type.set")
            return tasksForGroup(role, set_)
                .then(tasks => {
                    const batch = admin.firestore().batch();
                    tasks.forEach((v, _1, _2) => {
                        console.log(`Adding task ${v} to user:${userid}`)
                        const newRef = user_ref.collection('tasks').doc(v);
                        //batch.update(newRef , "annotations", admin.firestore.FieldValue.arrayUnion())
                        batch.set(newRef, {completed: admin.firestore.FieldValue.increment(0)}, {merge : true})
                        //batch.update(newRef, "completed", admin.firestore.FieldValue.increment(0))
                        })
                    return batch.commit()
                    })
                })
}

export const updateAllUsers = functions.pubsub.schedule('*/5 * * * *')
  .onRun(() => {
      console.log('This will be run every 5 minutes');
      admin.firestore().collection('users').get().then((doc) => {
          doc.forEach((user) => {
              console.log(`updating user ${user.id}`);
              updateTasksForUser(user.id);
              console.log("success")
          })
      }).catch(error => {
          console.log("there was an error updating users")
          console.log(error)
      });
      
  return null;
});


export const updateTasksOnGroupChange = functions.firestore.document('groups/{type}').onWrite((change, context) => {
    const groupType = context.params.type
    const data = change.after.data()
    if (data) {
        console.log(data)
        return usersForGroup(groupType, 0).then(res => {console.log(res)})
    }
    return null
})

export const makeUserEntry = functions.auth.user().onCreate((user) => {
    // get a set to assign user to
    const user_entry = {
        type: {
            role: "student",
            set: 0 // change this later
        },
        limits: {
            min: 3,
            max: 10000,
            types: []
        }
    };
    // need to update assignments here
    const result = admin.firestore()
        .collection('users')
        .doc(user.uid)
        .set(user_entry)
        .then(_ => {
            return updateTasksForUser(user.uid)
        });
    return result;
});

export const getTaskForUID = functions.https.onCall((_, context) => {
    /**
     * Get an incomplete task for a user
     */
    if (context && context.auth && context.auth.uid) {
        const uid = context.auth.uid;
        const tasks = admin.firestore().collection('tasks');
        const user = admin.firestore().collection('users').doc(uid).collection("tasks").where("completed", "<", 1).get().then(record => {
            if (!record.empty) {
                console.log(`Found: ${record.docs[0]}`)
                return tasks.doc(record.docs[0].id).get().then(res => {
                    console.log(res)
                    return {
                        id: res.id,
                        data: res.get("data")
                    }

                }).catch(error => {
                    console.log(error.error);
                    return null
                })
            } else {
                return null
            }
        }).catch(_error => {
            console.log("there was an error finding a record");
            return null
        });
        return user;
    } else {
        return null;
    }
});

/**
 * data contains a TaskId and an answer
 */
export const submitTask = functions.https.onCall((data, context) => {
    if (! (context && context.auth && context.auth.uid)) {
        return { status : "unable to validate login"};
    }
    const uuid = context.auth.uid;

    const taskId = data["task_id"];
    const answer = data["answer"];
    const meta = data["meta"];
    const user = admin.firestore().collection('users').doc(uuid);

    const annotations = admin.firestore().collection('annotations');
    return annotations.add({
        user_id: uuid,
        task_id: taskId,
        answer: answer,
        meta: meta,
        time: admin.firestore.Timestamp.now()
    }).then(doc => {
        // index annotation object
        // remove task_id from user's list
        return user.collection("tasks").doc(taskId).update({
            "annotations" : admin.firestore.FieldValue.arrayUnion(doc.id),
            "completed": admin.firestore.FieldValue.increment(1)
        }).then( _success => {
            console.log("success")
            return { status : "success" }
        }).catch( _fail1 => {
            console.log(_fail1)
            return { status : "failed to update assignment" }
        })
    }).catch( _fail2 => {
        // raise an issue
        return { status: "unable to create annotation entry" }
    });
});
