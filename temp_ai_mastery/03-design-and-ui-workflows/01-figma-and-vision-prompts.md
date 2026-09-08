# From Design to Code: AI Vision Workflows

Modern AI models (like GPT-4o, Claude 3.5 Sonnet, and Gemini 1.5 Pro) have powerful "vision" capabilities. You can feed them a screenshot of a UI or a Figma design, and they can output structured frontend code with high accuracy.

## The Vision Workflow

### Step 1: Prepare the Input
- **Screenshots:** Take a high-resolution screenshot of the component or page.
- **Figma:** Use "Export as Image" for a specific frame or take a clean screenshot of the Figma workspace.

### Step 2: Choose Your Model
- **Claude 3.5 Sonnet:** Currently widely considered the best for generating pixel-perfect frontend code and clean architecture.
- **GPT-4o:** Excellent for logical structure and general layout.

### Step 3: The "Design-to-Code" Prompt
Use the specific template for your target framework.

---

## Jetpack Compose (Android) Prompt
> "Act as an Expert Android Developer. Analyze the attached UI design. Generate a production-ready Jetpack Compose implementation.
>
> **Requirements:**
> - Use Material 3 components and theming.
> - Follow the MVI pattern (State, Event, Effect).
> - Use immutable data classes for UI state.
> - Ensure accessibility (content descriptions, touch targets).
> - Extract colors and spacing into a `Theme.kt` compatible format."

---

## React Native Prompt
> "Act as a Senior React Native Developer. Convert the attached UI design into a reusable component.
>
> **Requirements:**
> - Use TypeScript for all props and state.
> - Use Tailwind CSS (NativeWind) or Styled Components for styling.
> - Implement responsive layout using Flexbox.
> - Ensure the code is optimized for both iOS and Android.
> - Use Lucide-react-native or FontAwesome for icons."

---

## Flutter Prompt
> "Act as a Senior Flutter Developer. Transform the attached image into a Flutter widget.
>
> **Requirements:**
> - Use the latest Dart syntax and Material 3 widgets.
> - Follow a clean folder structure (widgets, models, providers).
> - Use `Riverpod` or `Bloc` for state management if the UI requires interaction.
> - Ensure the layout is adaptive for different screen sizes.
> - Provide a clear separation between the UI and business logic."

---

## Pro Tips for Production Code
1. **The "Style Guide" Prompt:** Before generating code, upload your project's `Theme.kt` or `tailwind.config.js` and say: *"Use the styles defined in this file for the following UI conversion."*
2. **Iterative Polishing:** If the AI misses a detail (e.g., a specific shadow or font weight), point it out: *"The button shadow is too subtle. Increase the elevation and adjust the blur radius to match the design."*
3. **Component Extraction:** Don't ask for a whole page at once. Feed the AI individual components (Buttons, Cards, Modals) for better code quality and modularity.
