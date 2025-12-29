import React, { useEffect, useState, useCallback, useMemo, memo } from "react";
import {
  FlatList,
  View,
  Text,
  Image,
  ActivityIndicator,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  ScrollView,
  TextInput,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import axios from "axios";

const api = axios.create({
  baseURL: "http://192.168.137.1:8000/api/",
});

const { width } = Dimensions.get("window");

// Memoized Icon Component
const Icon = memo(({ name, size = 24, color = "#333" }) => {
  const icons = {
    search: "🔍",
    cart: "🛒",
    filter: "⚙️",
    chevronRight: "➡️",
    tag: "🏷️",
    star: "⭐",
    starOutline: "☆",
  };
  
  return (
    <Text style={{ fontSize: size, color, lineHeight: size }}>
      {icons[name] || "◻️"}
    </Text>
  );
});

// Memoized Product Card Component
const ProductCard = memo(({ item, onAddToCart }) => {
  const handleAddToCart = useCallback(() => {
    onAddToCart(item);
  }, [item, onAddToCart]);

  return (
    <TouchableOpacity style={styles.productCard}>
      <View style={styles.productImageContainer}>
        {item.image ? (
          <Image 
            source={{ uri: item.image }} 
            style={styles.productImage} 
            resizeMode="cover" 
          />
        ) : (
          <View style={[styles.productImage, styles.imagePlaceholder]}>
            <Text style={styles.placeholderText}>No Image</Text>
          </View>
        )}
        {item.is_discounted && (
          <View style={styles.discountBadge}>
            <Text style={styles.discountText}>SALE</Text>
          </View>
        )}
        <TouchableOpacity 
          style={styles.cartButtonSmall} 
          onPress={handleAddToCart}
        >
          <Icon name="cart" size={16} color="#fff" />
        </TouchableOpacity>
      </View>

      <View style={styles.productInfo}>
        <Text style={styles.productCategory}>{item.category}</Text>
        <Text style={styles.productTitle} numberOfLines={2}>
          {item.title}
        </Text>

        <View style={styles.ratingContainer}>
          <Text style={styles.stars}>
            {"⭐".repeat(Math.floor(item.rating))}
            {"☆".repeat(5 - Math.floor(item.rating))}
          </Text>
          <Text style={styles.reviewCount}>({item.review_count})</Text>
        </View>

        <View style={styles.priceContainer}>
          <Text style={styles.currentPrice}>₵{item.price}</Text>
          {item.original_price && (
            <Text style={styles.originalPrice}>₵{item.original_price}</Text>
          )}
        </View>

        <View style={styles.stockStatus}>
          <View
            style={[
              styles.statusDot,
              {
                backgroundColor:
                  item.stock_status === "In stock" ? "#4CAF50" : "#FF5252",
              },
            ]}
          />
          <Text style={styles.statusText}>{item.stock_status}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
});

// Memoized Category Chip Component
const CategoryChip = memo(({ category, isActive, onPress }) => {
  const handlePress = useCallback(() => {
    onPress(category);
  }, [category, onPress]);

  return (
    <TouchableOpacity
      style={[
        styles.categoryChip,
        isActive && styles.categoryChipActive,
      ]}
      onPress={handlePress}
    >
      <Text style={styles.categoryIcon}>{category.icon}</Text>
      <Text style={[
        styles.categoryText,
        isActive && styles.categoryTextActive,
      ]}>
        {category.name}
      </Text>
    </TouchableOpacity>
  );
});

// Memoized Featured Product Card
const FeaturedProductCard = memo(({ product, onPress }) => {
  const handlePress = useCallback(() => {
    onPress(product);
  }, [product, onPress]);

  return (
    <TouchableOpacity 
      style={styles.featuredCard} 
      onPress={handlePress}
    >
      <Image
        source={{ uri: product.image }}
        style={styles.featuredImage}
      />
      <View style={styles.featuredInfo}>
        <Text style={styles.featuredTitle} numberOfLines={1}>
          {product.title}
        </Text>
        <Text style={styles.featuredPrice}>₵{product.price}</Text>
      </View>
    </TouchableOpacity>
  );
});

export default function App() {
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [cartCount, setCartCount] = useState(3);
  const [selectedCategory, setSelectedCategory] = useState(1);

  const categories = useMemo(() => [
    { id: 1, name: "All", icon: "🛒" },
    { id: 2, name: "Electronics", icon: "📱" },
    { id: 3, name: "Fashion", icon: "👕" },
    { id: 4, name: "Home & Garden", icon: "🏠" },
    { id: 5, name: "Books", icon: "📚" },
    { id: 6, name: "Health", icon: "💊" },
  ], []);

  useEffect(() => {
    async function fetchProducts() {
      try {
        const res = await api.get("products/");

        const formatted = res.data.map((p) => ({
          id: p.id || p.upc,
          title: p.title || "Product Title",
          upc: p.upc ? p.upc.toString() : "N/A",
          price:
            p.price !== null && p.price !== undefined
              ? Number(p.price).toFixed(2)
              : "0.00",
          original_price: p.original_price
            ? Number(p.original_price).toFixed(2)
            : null,
          image: p.image || p.primary_image || null,
          rating: p.rating || Math.random() * 2 + 3,
          review_count: p.review_count || Math.floor(Math.random() * 100),
          is_discounted: p.is_discounted || false,
          stock_status: p.stock_status || "In stock",
          category: p.category || "General",
          category_id: categories.find(c => c.name === p.category)?.id || 1,
          attributes: p.attributes || {},
        }));

        setProducts(formatted);
        setFilteredProducts(formatted);
      } catch (err) {
        console.error("Products error:", err?.response?.data || err?.message || err);
        setError(err?.response?.data || err?.message || "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    fetchProducts();
  }, [categories]);

  // Filter products based on search and category
  useEffect(() => {
    let filtered = [...products];
    
    if (selectedCategory !== 1) {
      const categoryName = categories.find(c => c.id === selectedCategory)?.name;
      filtered = filtered.filter(p => 
        p.category === categoryName || p.category_id === selectedCategory
      );
    }
    
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(p => 
        p.title.toLowerCase().includes(query) ||
        p.category.toLowerCase().includes(query)
      );
    }
    
    setFilteredProducts(filtered);
  }, [searchQuery, selectedCategory, products, categories]);

  const featuredProducts = useMemo(() => 
    products.slice(0, 3).filter(p => p.image), 
    [products]
  );

  const handleAddToCart = useCallback((product) => {
    console.log("Adding to cart:", product.title);
    setCartCount(prev => prev + 1);
    // Add your cart logic here
  }, []);

  const handleCategoryPress = useCallback((category) => {
    setSelectedCategory(category.id);
  }, []);

  const handleProductPress = useCallback((product) => {
    console.log("Product pressed:", product.title);
    // Navigate to product detail screen
  }, []);

  const renderProductItem = useCallback(({ item }) => (
    <ProductCard 
      item={item} 
      onAddToCart={handleAddToCart}
    />
  ), [handleAddToCart]);

  const renderCategoryItem = useCallback(({ item: category }) => (
    <CategoryChip
      category={category}
      isActive={selectedCategory === category.id}
      onPress={handleCategoryPress}
    />
  ), [selectedCategory, handleCategoryPress]);

  const renderFeaturedItem = useCallback(({ item }) => (
    <FeaturedProductCard
      product={item}
      onPress={handleProductPress}
    />
  ), [handleProductPress]);

  const keyExtractor = useCallback((item) => item.id.toString(), []);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6C63FF" />
        <Text style={styles.loadingText}>Loading products...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Oops!</Text>
          <Text style={styles.errorText}>
            Unable to load products. Please check your connection.
          </Text>
          <TouchableOpacity 
            style={styles.retryButton} 
            onPress={() => setLoading(true)}
          >
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Hello, Welcome 👋</Text>
          <Text style={styles.headerTitle}>Find amazing products</Text>
        </View>
        <TouchableOpacity style={styles.cartIconContainer}>
          <Icon name="cart" size={24} color="#333" />
          {cartCount > 0 && (
            <View style={styles.cartBadge}>
              <Text style={styles.cartBadgeText}>{cartCount}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchInputContainer}>
          <Icon name="search" size={20} color="#666" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search products, brands..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholderTextColor="#999"
            returnKeyType="search"
            clearButtonMode="while-editing"
          />
          <TouchableOpacity style={styles.filterButton}>
            <Icon name="filter" size={20} color="#666" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Categories */}
      <FlatList
        data={categories}
        renderItem={renderCategoryItem}
        keyExtractor={(item) => item.id.toString()}
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.categoriesContainer}
        contentContainerStyle={styles.categoriesContent}
        initialNumToRender={6}
        maxToRenderPerBatch={10}
        windowSize={5}
      />

      {/* Featured Section */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Featured Products</Text>
        <TouchableOpacity style={styles.seeAllButton}>
          <Text style={styles.seeAllText}>See All</Text>
          <Icon name="chevronRight" size={16} color="#6C63FF" />
        </TouchableOpacity>
      </View>

      <FlatList
        data={featuredProducts}
        renderItem={renderFeaturedItem}
        keyExtractor={keyExtractor}
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.featuredContainer}
        contentContainerStyle={styles.featuredContent}
        initialNumToRender={3}
        maxToRenderPerBatch={5}
        windowSize={3}
      />

      {/* Products Grid */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>All Products</Text>
        <Text style={styles.productCount}>{filteredProducts.length} items</Text>
      </View>

      <FlatList
        data={filteredProducts}
        renderItem={renderProductItem}
        keyExtractor={keyExtractor}
        numColumns={2}
        columnWrapperStyle={styles.productsGrid}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.productsContainer}
        initialNumToRender={8}
        maxToRenderPerBatch={10}
        windowSize={10}
        removeClippedSubviews={true}
        updateCellsBatchingPeriod={50}
        onEndReachedThreshold={0.5}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F8F9FA",
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#F8F9FA",
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: "#666",
  },
  errorContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  errorTitle: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#333",
    marginBottom: 10,
  },
  errorText: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: "#6C63FF",
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 25,
  },
  retryButtonText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 16,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 20,
  },
  greeting: {
    fontSize: 14,
    color: "#666",
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#333",
  },
  cartIconContainer: {
    position: "relative",
  },
  cartBadge: {
    position: "absolute",
    top: -5,
    right: -5,
    backgroundColor: "#FF5252",
    borderRadius: 10,
    width: 20,
    height: 20,
    justifyContent: "center",
    alignItems: "center",
  },
  cartBadgeText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "bold",
  },
  searchContainer: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  searchInputContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  searchIcon: {
    marginRight: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: "#333",
  },
  filterButton: {
    marginLeft: 12,
  },
  categoriesContainer: {
    marginBottom: 24,
    paddingLeft: 20,
  },
  categoriesContent: {
    paddingRight: 20,
  },
  categoryChip: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginRight: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  categoryChipActive: {
    backgroundColor: "#6C63FF",
  },
  categoryIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  categoryText: {
    fontSize: 14,
    fontWeight: "500",
    color: "#333",
  },
  categoryTextActive: {
    color: "#fff",
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#333",
  },
  productCount: {
    fontSize: 14,
    color: "#666",
  },
  seeAllButton: {
    flexDirection: "row",
    alignItems: "center",
  },
  seeAllText: {
    fontSize: 14,
    color: "#6C63FF",
    fontWeight: "500",
    marginRight: 4,
  },
  featuredContainer: {
    marginBottom: 24,
    paddingLeft: 20,
  },
  featuredContent: {
    paddingRight: 20,
  },
  featuredCard: {
    width: width * 0.6,
    backgroundColor: "#fff",
    borderRadius: 16,
    marginRight: 16,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  featuredImage: {
    width: "100%",
    height: 150,
  },
  featuredInfo: {
    padding: 12,
  },
  featuredTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#333",
    marginBottom: 6,
  },
  featuredPrice: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#6C63FF",
  },
  productsContainer: {
    paddingHorizontal: 20,
    paddingBottom: 100,
  },
  productsGrid: {
    justifyContent: "space-between",
    marginBottom: 16,
  },
  productCard: {
    width: (width - 48) / 2,
    backgroundColor: "#fff",
    borderRadius: 16,
    overflow: "hidden",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  productImageContainer: {
    position: "relative",
  },
  productImage: {
    width: "100%",
    height: 150,
  },
  imagePlaceholder: {
    backgroundColor: "#F0F0F0",
    justifyContent: "center",
    alignItems: "center",
  },
  placeholderText: {
    color: "#999",
    fontSize: 14,
  },
  discountBadge: {
    position: "absolute",
    top: 12,
    left: 12,
    backgroundColor: "#FF5252",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  discountText: {
    color: "#fff",
    fontSize: 10,
    fontWeight: "bold",
  },
  cartButtonSmall: {
    position: "absolute",
    bottom: -12,
    right: 12,
    backgroundColor: "#6C63FF",
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
  },
  productInfo: {
    padding: 12,
  },
  productCategory: {
    fontSize: 10,
    color: "#666",
    marginBottom: 4,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  productTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
    marginBottom: 8,
    lineHeight: 18,
  },
  ratingContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
  },
  stars: {
    fontSize: 12,
    color: "#FFD700",
    marginRight: 6,
  },
  reviewCount: {
    fontSize: 12,
    color: "#666",
  },
  priceContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
  },
  currentPrice: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#333",
  },
  originalPrice: {
    fontSize: 14,
    color: "#999",
    textDecorationLine: "line-through",
    marginLeft: 8,
  },
  stockStatus: {
    flexDirection: "row",
    alignItems: "center",
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
    color: "#666",
  },
});