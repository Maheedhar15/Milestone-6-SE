<template>
  <div class="container">
    <div class="topic-container">
      <h3>ADD ADMIN BY EMAIL ID</h3>
    </div>
    <br />
    <form v-on:submit="addUser">
      <!-- <div class="row"> -->
      <!-- <div class="col-md-10"> -->
      <div class="form-group">
        <label>Enter Email ID</label
        ><input type="text" class="form-control" v-model="emailID" required />
      </div>
      <br />
      <div class="form-group">
        <label>Enter Username</label
        ><input type="text" class="form-control" v-model="username" required />
      </div>
      <br />
      <div class="form-group">
        <label>Enter Password</label
        ><input
          placeholder="Password must be a minimum of 10 characters"
          type="text"
          class="form-control"
          v-model="password"
          required
        />
      </div>
      <!-- </div> -->
      <!-- <br />
                <br />
                <br />
                <div class="col-md-10">
                    <input type="text" class="form-control" v-model="roleID" placeholder="Enter Role" required />
                </div> -->
      <br />
      <button class="btn btn-lg" @click="addUser" type="submit">Submit</button>
    </form>
    <hr />
  </div>
</template>
<script>
//import router from '@/router';
import axios from 'axios';
export default {
  name: 'AddAdminsComponent',
  data() {
    return {
      emailID: '',
      roleID: 3,
      username: '',
      password: '',
    };
  },
  methods: {
    async addUser(x) {
      // console.log(this.response)
      x.preventDefault();
      console.log(this.emailID);
      let c = this.emailID;
      var data = {
        email_id: c,
        role_id: this.roleID,
        username: this.username,
        password: this.password,
      };
      console.log(c);
      data = JSON.stringify(data);
      console.log('Data is :');
      console.log(data);
      await axios
        .post('/api/user', { data })
        .then((res) => {
          axios
            .post('/api/v1/discourse/create/user', { data })
            .then((res) => console.log(res))
            .catch((err) => {
              console.log(err);
            });
          alert('User has been successfully added.');
          this.$router.go();
          console.log(res);
        })
        .catch((err) => {
          console.log(err);
        });
    },
  },
};
</script>
<style scoped>
.topic-container {
  margin: 33px 63px;
}
.form-group {
  margin-bottom: 1.5rem;
}
</style>
