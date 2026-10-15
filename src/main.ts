import { mount } from 'svelte';
import App from './App.svelte';
import '@fontsource-variable/figtree/wght.css';
import '@fontsource-variable/league-spartan/wght.css';
import './styles.css';

mount(App, { target: document.getElementById('app')! });
