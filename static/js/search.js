// //radhashyam/ static/js/search.js
// document.getElementById('search-input').addEventListener('input', function (e) {
//     fetch(`/search/?q=${e.target.value}`)
//         .then(response => response.json())
//         .then(data => updateProductGrid(data));
// });

// function updateProductGrid(products) {
//     const container = document.getElementById('product-grid');
//     if (!container) return;

//     container.innerHTML = products.map(product => `
//         <div class="col-md-4 mb-4">
//             <div class="card product-card h-100">
//                 <img src="${product.image}" class="card-img-top product-thumbnail" alt="${product.title}">
//                 <div class="card-body">
//                     <h5 class="card-title">${product.title}</h5>
//                     <p class="card-text">₹${product.price}</p>
//                 </div>
//             </div>
//         </div>
//     `).join('');
// }