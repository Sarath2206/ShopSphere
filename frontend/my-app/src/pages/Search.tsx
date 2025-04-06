import React, { useState } from 'react';
import {
    Container,
    Paper,
    TextField,
    Button,
    Typography,
    Box,
    Card,
    CardMedia,
    CardContent,
    CircularProgress,
    Alert,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Slider,
    Chip,
} from '@mui/material';
import searchService, { SearchFilters, ClothingItem } from '../services/searchService';

const Search: React.FC = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<ClothingItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [filters, setFilters] = useState<SearchFilters>({
        size: '',
        color: '',
        minPrice: 0,
        maxPrice: 10000,
        gender: '',
        material: '',
    });

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError('');
        try {
            const data = await searchService.search(query, filters);
            setResults(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const handleFilterChange = (name: keyof SearchFilters, value: any) => {
        setFilters(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const clearFilters = () => {
        setFilters({
            size: '',
            color: '',
            minPrice: 0,
            maxPrice: 10000,
            gender: '',
            material: '',
        });
    };

    return (
        <Container maxWidth="lg">
            <Box sx={{ mt: 4, mb: 4 }}>
                <Paper elevation={3} sx={{ p: 4 }}>
                    <Typography variant="h4" component="h1" gutterBottom align="center">
                        AI Clothing Comparator
                    </Typography>
                    <form onSubmit={handleSearch}>
                        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' }, gap: 2 }}>
                            <Box>
                                <TextField
                                    fullWidth
                                    label="Search Query"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder="e.g., black shirt in medium size from Meesho, Nykaa and Fab India"
                                />
                            </Box>
                            <Box>
                                <Button
                                    type="submit"
                                    variant="contained"
                                    fullWidth
                                    disabled={loading}
                                    sx={{ height: '56px' }}
                                >
                                    {loading ? <CircularProgress size={24} /> : 'Search'}
                                </Button>
                            </Box>
                        </Box>

                        <Box sx={{ mt: 4 }}>
                            <Typography variant="h6" gutterBottom>
                                Filters
                            </Typography>
                            <Box sx={{ 
                                display: 'grid', 
                                gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' },
                                gap: 2 
                            }}>
                                <Box>
                                    <FormControl fullWidth>
                                        <InputLabel>Size</InputLabel>
                                        <Select
                                            value={filters.size}
                                            label="Size"
                                            onChange={(e) => handleFilterChange('size', e.target.value)}
                                        >
                                            <MenuItem value="">Any</MenuItem>
                                            <MenuItem value="S">Small</MenuItem>
                                            <MenuItem value="M">Medium</MenuItem>
                                            <MenuItem value="L">Large</MenuItem>
                                            <MenuItem value="XL">Extra Large</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Box>
                                <Box>
                                    <FormControl fullWidth>
                                        <InputLabel>Color</InputLabel>
                                        <Select
                                            value={filters.color}
                                            label="Color"
                                            onChange={(e) => handleFilterChange('color', e.target.value)}
                                        >
                                            <MenuItem value="">Any</MenuItem>
                                            <MenuItem value="black">Black</MenuItem>
                                            <MenuItem value="white">White</MenuItem>
                                            <MenuItem value="blue">Blue</MenuItem>
                                            <MenuItem value="red">Red</MenuItem>
                                            <MenuItem value="green">Green</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Box>
                                <Box>
                                    <FormControl fullWidth>
                                        <InputLabel>Gender</InputLabel>
                                        <Select
                                            value={filters.gender}
                                            label="Gender"
                                            onChange={(e) => handleFilterChange('gender', e.target.value)}
                                        >
                                            <MenuItem value="">Any</MenuItem>
                                            <MenuItem value="men">Men</MenuItem>
                                            <MenuItem value="women">Women</MenuItem>
                                            <MenuItem value="unisex">Unisex</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Box>
                                <Box sx={{ gridColumn: { xs: '1', sm: '1 / -1' } }}>
                                    <Typography gutterBottom>Price Range</Typography>
                                    <Slider
                                        value={[filters.minPrice || 0, filters.maxPrice || 10000]}
                                        onChange={(_, newValue) => {
                                            if (Array.isArray(newValue)) {
                                                handleFilterChange('minPrice', newValue[0]);
                                                handleFilterChange('maxPrice', newValue[1]);
                                            }
                                        }}
                                        valueLabelDisplay="auto"
                                        min={0}
                                        max={10000}
                                        step={100}
                                    />
                                </Box>
                                <Box sx={{ gridColumn: { xs: '1', sm: '1 / -1' } }}>
                                    <Button
                                        variant="outlined"
                                        onClick={clearFilters}
                                    >
                                        Clear Filters
                                    </Button>
                                </Box>
                            </Box>
                        </Box>
                    </form>
                </Paper>

                {error && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                        {error}
                    </Alert>
                )}

                {loading && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                        <CircularProgress />
                    </Box>
                )}

                {results.length > 0 && (
                    <Box sx={{ 
                        display: 'grid', 
                        gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' },
                        gap: 3,
                        mt: 4 
                    }}>
                        {results.map((item) => (
                            <Box key={item.id}>
                                <Card>
                                    <CardMedia
                                        component="img"
                                        height="200"
                                        image={item.image_url}
                                        alt={item.title}
                                        sx={{ objectFit: 'contain' }}
                                    />
                                    <CardContent>
                                        <Typography gutterBottom variant="h6" component="div">
                                            {item.title}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            Price: ₹{item.price}
                                        </Typography>
                                        {item.size && (
                                            <Chip
                                                label={`Size: ${item.size}`}
                                                size="small"
                                                sx={{ mr: 1, mt: 1 }}
                                            />
                                        )}
                                        {item.color && (
                                            <Chip
                                                label={`Color: ${item.color}`}
                                                size="small"
                                                sx={{ mr: 1, mt: 1 }}
                                            />
                                        )}
                                        {item.material && (
                                            <Chip
                                                label={`Material: ${item.material}`}
                                                size="small"
                                                sx={{ mr: 1, mt: 1 }}
                                            />
                                        )}
                                        <Chip
                                            label={item.source_website}
                                            color="primary"
                                            size="small"
                                            sx={{ mt: 1 }}
                                        />
                                        <Box sx={{ mt: 2 }}>
                                            <Button
                                                variant="contained"
                                                size="small"
                                                href={item.product_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                            >
                                                View Product
                                            </Button>
                                        </Box>
                                    </CardContent>
                                </Card>
                            </Box>
                        ))}
                    </Box>
                )}
            </Box>
        </Container>
    );
};

export default Search; 