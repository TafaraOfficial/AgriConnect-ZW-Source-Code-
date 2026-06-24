const mongoose = require("mongoose");

const ProductSchema = new mongoose.Schema({

    farmer:{
        type:mongoose.Schema.Types.ObjectId,
        ref:"User"
    },

    productName:String,

    category:String,

    quantity:Number,

    unit:String,

    price:Number,

    location:String,

    image:String,

    createdAt:{
        type:Date,
        default:Date.now
    }

});

module.exports = mongoose.model(
 "Product",
 ProductSchema
);