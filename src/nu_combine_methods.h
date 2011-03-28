/*
 * Copyright 2008-2011 Sergio Pascual
 *
 * This file is part of PyEmir
 *
 * PyEmir is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * PyEmir is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with PyEmir.  If not, see <http://www.gnu.org/licenses/>.
 *
 */


#ifndef NU_COMBINE_METHODS_H
#define NU_COMBINE_METHODS_H

#include "nu_combine_defs.h"

int NU_mean_function(double *data, double *weights,
    int size, double *out[NU_COMBINE_OUTDIM], void *func_data);

#endif // NU_COMBINE_METHODS_H