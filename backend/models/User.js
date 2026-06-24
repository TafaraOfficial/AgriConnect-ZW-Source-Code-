const mongoose = require("mongoose");

const UserSchema = new mongoose.Schema({
    fullName:{
        type:String,
        required:true
    },

    email:{
        type:String,
        required:true,
        unique:true
    },

    password:{
        type:String,
        required:true
    },

    role:{
        type:String,
        enum:["Farmer","Buyer","Supplier","Admin"],
        default:"Farmer"
    },

    phone:{
        type:String
    },

    location:{
        type:String
    },

    createdAt:{
        type:Date,
        default:Date.now
    }
});

module.exports = mongoose.model("User",UserSchema);