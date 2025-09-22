/**
 * BookingFlowRouter - Manages dynamic booking flow based on service configuration
 * 
 * This router handles the navigation logic for different service types,
 * allowing for flexible flows that can be configured per service category.
 */

class BookingFlowRouter {
    constructor(serviceConfig) {
        this.serviceConfig = serviceConfig || {};
        this.bookingRequirements = serviceConfig.booking_requirements || {};
        this.flowType = this.bookingRequirements.flow_type || 'standard';
        this.currentIndex = 0;
        this.screens = this.buildScreenSequence();
        this.skipConditions = this.bookingRequirements.skip_conditions || {};
    }

    /**
     * Flow type definitions
     */
    static FLOW_TYPES = {
        'standard': {
            screens: ['address', 'schedule', 'worker', 'payment', 'confirmation'],
            pricing: 'fixed'
        },
        'property_based': {
            screens: ['address', 'property_typology', 'schedule', 'worker', 'payment', 'confirmation'],
            pricing: 'typology_based'
        },
        'unit_based': {
            screens: ['address', 'unit_count', 'schedule', 'worker', 'payment', 'confirmation'],
            pricing: 'per_unit'
        },
        'time_based': {
            screens: ['address', 'duration', 'schedule', 'worker', 'payment', 'confirmation'],
            pricing: 'hourly'
        },
        'package_based': {
            screens: ['address', 'package_selection', 'schedule', 'worker', 'payment', 'confirmation'],
            pricing: 'package'
        },
        'custom': {
            screens: [], // Fully defined in booking_requirements
            pricing: 'custom'
        }
    };

    /**
     * Build the screen sequence based on flow type and custom requirements
     */
    buildScreenSequence() {
        let baseScreens = BookingFlowRouter.FLOW_TYPES[this.flowType]?.screens || [];
        
        // If custom flow or has custom screens, merge them
        if (this.bookingRequirements.required_screens) {
            if (this.flowType === 'custom') {
                baseScreens = this.bookingRequirements.required_screens.map(s => 
                    typeof s === 'string' ? s : s.name
                );
            } else {
                // Merge custom screens into the base flow
                baseScreens = this.mergeScreens(baseScreens, this.bookingRequirements.required_screens);
            }
        }

        // Add optional screens if conditions are met
        if (this.bookingRequirements.optional_screens) {
            baseScreens = this.addOptionalScreens(baseScreens, this.bookingRequirements.optional_screens);
        }

        return baseScreens;
    }

    /**
     * Merge custom screens into base flow at appropriate positions
     */
    mergeScreens(baseScreens, customScreens) {
        const result = [...baseScreens];
        
        customScreens.forEach(screen => {
            const screenName = typeof screen === 'string' ? screen : screen.name;
            const position = typeof screen === 'object' ? screen.position : null;
            
            if (!result.includes(screenName)) {
                if (position && position.after) {
                    const index = result.indexOf(position.after);
                    if (index !== -1) {
                        result.splice(index + 1, 0, screenName);
                    } else {
                        result.push(screenName);
                    }
                } else if (position && position.before) {
                    const index = result.indexOf(position.before);
                    if (index !== -1) {
                        result.splice(index, 0, screenName);
                    } else {
                        result.push(screenName);
                    }
                } else {
                    // Default: add before schedule
                    const scheduleIndex = result.indexOf('schedule');
                    if (scheduleIndex !== -1) {
                        result.splice(scheduleIndex, 0, screenName);
                    } else {
                        result.push(screenName);
                    }
                }
            }
        });
        
        return result;
    }

    /**
     * Add optional screens based on conditions
     */
    addOptionalScreens(baseScreens, optionalScreens) {
        const result = [...baseScreens];
        
        optionalScreens.forEach(screen => {
            const screenName = typeof screen === 'string' ? screen : screen.name;
            const condition = typeof screen === 'object' ? screen.condition : null;
            
            // For now, add all optional screens - condition evaluation will happen at runtime
            if (!result.includes(screenName)) {
                const position = typeof screen === 'object' ? screen.position : null;
                
                if (position && position.after) {
                    const index = result.indexOf(position.after);
                    if (index !== -1) {
                        result.splice(index + 1, 0, screenName);
                    }
                } else if (position && position.before) {
                    const index = result.indexOf(position.before);
                    if (index !== -1) {
                        result.splice(index, 0, screenName);
                    }
                }
            }
        });
        
        return result;
    }

    /**
     * Get the current screen
     */
    getCurrentScreen() {
        return this.screens[this.currentIndex];
    }

    /**
     * Get the next screen, handling skip conditions
     */
    getNextScreen(bookingData) {
        let nextIndex = this.currentIndex + 1;
        
        // Skip screens based on conditions
        while (nextIndex < this.screens.length) {
            const screenName = this.screens[nextIndex];
            if (!this.shouldSkipScreen(screenName, bookingData)) {
                this.currentIndex = nextIndex;
                return screenName;
            }
            nextIndex++;
        }
        
        return null; // No more screens
    }

    /**
     * Get the previous screen, handling skip conditions
     */
    getPreviousScreen(bookingData) {
        let prevIndex = this.currentIndex - 1;
        
        // Skip screens based on conditions
        while (prevIndex >= 0) {
            const screenName = this.screens[prevIndex];
            if (!this.shouldSkipScreen(screenName, bookingData)) {
                this.currentIndex = prevIndex;
                return screenName;
            }
            prevIndex--;
        }
        
        return null; // No previous screen
    }

    /**
     * Check if a screen should be skipped based on conditions
     */
    shouldSkipScreen(screenName, bookingData) {
        // Check skip conditions from configuration
        const skipCondition = this.skipConditions[screenName];
        if (!skipCondition) return false;
        
        // Evaluate condition based on booking data
        if (typeof skipCondition === 'function') {
            return skipCondition(bookingData);
        }
        
        // Handle object-based conditions
        if (typeof skipCondition === 'object') {
            const { field, operator, value } = skipCondition;
            const fieldValue = this.getNestedValue(bookingData, field);
            
            switch (operator) {
                case 'equals':
                    return fieldValue === value;
                case 'not_equals':
                    return fieldValue !== value;
                case 'in':
                    return Array.isArray(value) && value.includes(fieldValue);
                case 'not_in':
                    return Array.isArray(value) && !value.includes(fieldValue);
                case 'exists':
                    return fieldValue !== undefined && fieldValue !== null;
                case 'not_exists':
                    return fieldValue === undefined || fieldValue === null;
                default:
                    return false;
            }
        }
        
        return false;
    }

    /**
     * Get nested value from object using dot notation
     */
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => current?.[key], obj);
    }

    /**
     * Jump to a specific screen by name
     */
    goToScreen(screenName) {
        const index = this.screens.indexOf(screenName);
        if (index !== -1) {
            this.currentIndex = index;
            return screenName;
        }
        return null;
    }

    /**
     * Get screen configuration
     */
    getScreenConfig(screenName) {
        // Find screen configuration in required_screens or optional_screens
        const requiredScreen = this.bookingRequirements.required_screens?.find(
            s => (typeof s === 'string' ? s : s.name) === screenName
        );
        
        if (requiredScreen && typeof requiredScreen === 'object') {
            return requiredScreen;
        }
        
        const optionalScreen = this.bookingRequirements.optional_screens?.find(
            s => (typeof s === 'string' ? s : s.name) === screenName
        );
        
        if (optionalScreen && typeof optionalScreen === 'object') {
            return optionalScreen;
        }
        
        // Return default configuration
        return {
            name: screenName,
            component: null,
            config: {}
        };
    }

    /**
     * Get the progress percentage
     */
    getProgress() {
        if (this.screens.length === 0) return 0;
        return Math.round(((this.currentIndex + 1) / this.screens.length) * 100);
    }

    /**
     * Check if current screen is the last one
     */
    isLastScreen() {
        return this.currentIndex === this.screens.length - 1;
    }

    /**
     * Check if current screen is the first one
     */
    isFirstScreen() {
        return this.currentIndex === 0;
    }

    /**
     * Reset router to first screen
     */
    reset() {
        this.currentIndex = 0;
    }

    /**
     * Get all screens in the flow
     */
    getAllScreens() {
        return [...this.screens];
    }

    /**
     * Get validation rules for current screen
     */
    getValidationRules(screenName) {
        const config = this.getScreenConfig(screenName);
        return config.validation || {};
    }

    /**
     * Get pricing model for the service
     */
    getPricingModel() {
        return this.bookingRequirements.pricing_model || 
               BookingFlowRouter.FLOW_TYPES[this.flowType]?.pricing || 
               'fixed';
    }
}